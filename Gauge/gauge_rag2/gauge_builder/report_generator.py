"""
report_generator.py
===================
Generates a rich AI-powered HTML report from Gauge test results.

HOW IT WORKS:
  Best method — save gauge console output to a file, then run this script:
      gauge run specs 2>&1 | tee gauge_output.txt
      python gauge_builder/report_generator.py --from-output gauge_output.txt

  Auto mode (tries to read index.html or any result JSON):
      python gauge_builder/report_generator.py

USAGE:
  python gauge_builder/report_generator.py
  python gauge_builder/report_generator.py --from-output gauge_output.txt
  python gauge_builder/report_generator.py --output reports/ai_report.html
"""

import json
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime


# ---------------------------------------------------------------------------
# Parse Gauge console output  (most reliable source)
# ---------------------------------------------------------------------------

def parse_console_output(text: str) -> dict:
    summary = _empty_summary()

    scenario_pattern  = re.compile(r'##\s+(.+?)\s+((?:[PF]\s*)+)$', re.MULTILINE)
    failed_step_pat   = re.compile(
        r'Failed Step:\s*(.+?)\n.*?Error Message:\s*(.+?)(?=\n\n|\n  ##|\Z)', re.DOTALL)
    spec_summary_pat  = re.compile(
        r'Specifications:\s*(\d+) executed\s+(\d+) passed\s+(\d+) failed\s+(\d+) skipped')
    scen_summary_pat  = re.compile(
        r'Scenarios:\s*(\d+) executed\s+(\d+) passed\s+(\d+) failed\s+(\d+) skipped')
    time_pat          = re.compile(r'Total time taken:\s*(.+)')

    # Map failed steps to their scenario
    failed_steps_by_sc = {}
    for m in failed_step_pat.finditer(text):
        step_text  = m.group(1).strip()
        error_text = m.group(2).strip()[:300]
        preceding  = text[:m.start()]
        sc_matches = list(re.finditer(r'##\s+(.+?)\s+[PF]', preceding))
        if sc_matches:
            sc_name = sc_matches[-1].group(1).strip()
            failed_steps_by_sc.setdefault(sc_name, []).append(
                {"step": step_text, "error": error_text})
            summary["failures"].append(
                {"scenario": sc_name, "step": step_text, "error": error_text})

    current_spec = {"name": "Test Suite", "failed": False, "scenarios": [], "execution_time": 0}

    for m in scenario_pattern.finditer(text):
        sc_name   = m.group(1).strip()
        steps     = m.group(2).strip().split()
        failed    = "F" in steps

        sc_info = {
            "name": sc_name, "failed": failed, "skipped": False,
            "failed_steps": failed_steps_by_sc.get(sc_name, []),
            "execution_time": 0,
            "tags": _guess_tags(sc_name),
        }
        current_spec["scenarios"].append(sc_info)
        summary["total_scenarios"] += 1
        summary["total_steps"]     += len(steps)
        summary["passed_steps"]    += steps.count("P")
        summary["failed_steps"]    += steps.count("F")

        if failed:
            summary["failed_scenarios"] += 1
            current_spec["failed"] = True
        else:
            summary["passed_scenarios"] += 1

        module = _extract_module(sc_name)
        summary["modules"].setdefault(module, {"passed": 0, "failed": 0, "skipped": 0})
        summary["modules"][module]["failed" if failed else "passed"] += 1

    if current_spec["scenarios"]:
        summary["specs"].append(current_spec)
        summary["total_specs"]  = 1
        summary["failed_specs"] = 1 if current_spec["failed"] else 0
        summary["passed_specs"] = 0 if current_spec["failed"] else 1

    # Override totals with official summary line
    m = spec_summary_pat.search(text)
    if m:
        summary["total_specs"]   = int(m.group(1))
        summary["passed_specs"]  = int(m.group(2))
        summary["failed_specs"]  = int(m.group(3))

    m = scen_summary_pat.search(text)
    if m:
        summary["total_scenarios"]   = int(m.group(1))
        summary["passed_scenarios"]  = int(m.group(2))
        summary["failed_scenarios"]  = int(m.group(3))
        summary["skipped_scenarios"] = int(m.group(4))

    m = time_pat.search(text)
    if m:
        summary["execution_time_str"] = m.group(1).strip()
        summary["execution_time_ms"]  = _parse_time_to_ms(m.group(1).strip())

    return summary


# ---------------------------------------------------------------------------
# Parse Gauge JSON result
# ---------------------------------------------------------------------------

def _parse_json_result(raw: dict) -> dict:
    summary = _empty_summary()
    spec_results = (raw.get("specResults") or
                    raw.get("suiteResult", {}).get("specResults") or [])

    for spec in spec_results:
        summary["total_specs"] += 1
        spec_name   = spec.get("specHeading", spec.get("heading", "Unknown"))
        spec_failed = spec.get("failed", False)
        summary["failed_specs" if spec_failed else "passed_specs"] += 1

        spec_info = {"name": spec_name, "failed": spec_failed,
                     "scenarios": [], "execution_time": spec.get("executionTime", 0)}

        for sc in spec.get("scenarioResults", spec.get("scenarios", [])):
            summary["total_scenarios"] += 1
            sc_name   = sc.get("scenarioHeading", sc.get("heading", "Unknown"))
            sc_failed = sc.get("failed", False)
            sc_skip   = sc.get("skipped", False)

            if sc_skip:     summary["skipped_scenarios"] += 1
            elif sc_failed: summary["failed_scenarios"]  += 1
            else:           summary["passed_scenarios"]  += 1

            failed_steps = []
            for step in sc.get("stepResults", sc.get("steps", [])):
                summary["total_steps"] += 1
                if step.get("failed", False):
                    summary["failed_steps"] += 1
                    err = step.get("errorMessage", step.get("error", ""))[:300]
                    failed_steps.append({"step": step.get("stepText", ""), "error": err})
                    summary["failures"].append(
                        {"scenario": sc_name, "step": step.get("stepText", ""), "error": err})
                else:
                    summary["passed_steps"] += 1

            sc_info = {
                "name": sc_name, "failed": sc_failed, "skipped": sc_skip,
                "failed_steps": failed_steps,
                "execution_time": sc.get("executionTime", 0),
                "tags": sc.get("tags", []),
            }
            spec_info["scenarios"].append(sc_info)

            module = _extract_module(sc_name)
            summary["modules"].setdefault(module, {"passed": 0, "failed": 0, "skipped": 0})
            if sc_skip:     summary["modules"][module]["skipped"] += 1
            elif sc_failed: summary["modules"][module]["failed"]  += 1
            else:           summary["modules"][module]["passed"]  += 1

        summary["specs"].append(spec_info)
        summary["execution_time_ms"] += spec.get("executionTime", 0)

    summary["execution_time_str"] = _ms_to_str(summary["execution_time_ms"])
    return summary


def _try_parse_file(path: Path) -> dict:
    """Try to parse a JSON/JS result file with various wrapper stripping."""
    text = path.read_text(encoding="utf-8", errors="ignore").strip()
    for strip_fn in [
        lambda t: t[len("gauge_publish_message("):].rstrip(")"),
        lambda t: t.split("=", 1)[-1].strip().rstrip(";"),
        lambda t: t,
    ]:
        try:
            data = json.loads(strip_fn(text))
            if any(k in data for k in ("specResults", "suiteResult")):
                return _parse_json_result(data)
        except Exception:
            continue
    return None


def parse_index_html(html_path: Path) -> dict:
    """Try to extract JSON from Gauge's index.html."""
    text = html_path.read_text(encoding="utf-8", errors="ignore")

    # Try inline JSON blobs
    for pat in [
        r'gauge_publish_message\((\{.+?\})\)',
        r'window\.\w+\s*=\s*(\{.+?\})\s*;',
        r'(\{"suiteResult".+?\})\s*[;\)]',
        r'(\{"specResults".+?\})\s*[;\)]',
    ]:
        for m in re.finditer(pat, text, re.DOTALL):
            try:
                data = json.loads(m.group(1))
                if any(k in data for k in ("specResults", "suiteResult")):
                    return _parse_json_result(data)
            except Exception:
                continue

    # Check referenced JS files
    for js_file in re.findall(r'<script[^>]+src=["\']js/([^"\']+)["\']', text):
        js_path = html_path.parent / "js" / js_file
        if js_path.exists():
            result = _try_parse_file(js_path)
            if result:
                return result

    return None


def find_result_source(project_root: Path):
    """Return (kind, path) of the best available result source."""
    for rel in [
        "reports/html-report/js/result.json",
        "reports/last_run/result/last.json",
        "reports/last_run/result.json",
        "reports/result.json",
    ]:
        p = project_root / rel
        if p.exists() and p.stat().st_size > 100:
            return ("json", p)

    reports = project_root / "reports"
    if reports.exists():
        for f in sorted(reports.rglob("*.js")) + sorted(reports.rglob("*.json")):
            if f.stat().st_size < 100:
                continue
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
                if "specResults" in t or "suiteResult" in t:
                    return ("json", f)
            except Exception:
                pass

    idx = project_root / "reports" / "html-report" / "index.html"
    if idx.exists():
        return ("html", idx)

    return (None, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empty_summary() -> dict:
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_specs": 0, "passed_specs": 0, "failed_specs": 0,
        "total_scenarios": 0, "passed_scenarios": 0,
        "failed_scenarios": 0, "skipped_scenarios": 0,
        "total_steps": 0, "passed_steps": 0, "failed_steps": 0,
        "execution_time_ms": 0, "execution_time_str": "—",
        "specs": [], "failures": [], "modules": {},
    }


def _extract_module(sc_name: str) -> str:
    prefix = sc_name.split(":")[0].strip()
    prefix = re.sub(r'_TC_?\d*$', '', prefix)
    prefix = re.sub(r'_\d+$', '', prefix)
    return prefix.replace("_", " ").title()


def _guess_tags(sc_name: str) -> list:
    lower = sc_name.lower()
    return [t for t in ("happy_path", "negative", "boundary", "e2e")
            if t.replace("_", " ") in lower or t in lower]


def _parse_time_to_ms(s: str) -> int:
    total = 0
    for val, unit in re.findall(r'([\d.]+)([hms])', s):
        v = float(val)
        total += v * {"h": 3600000, "m": 60000, "s": 1000}[unit]
    return int(total)


def _ms_to_str(ms: int) -> str:
    s = ms / 1000
    if s >= 60:
        return f"{int(s//60)}m{s%60:.1f}s"
    return f"{s:.1f}s"


# ---------------------------------------------------------------------------
# AI Analysis
# ---------------------------------------------------------------------------

def analyze_with_claude(summary: dict) -> dict:
    try:
        import urllib.request
        prompt = f"""You are a senior QA engineer analyzing automated test results for calculator.net.

TEST RESULTS:
- Total Scenarios: {summary['total_scenarios']}
- Passed: {summary['passed_scenarios']}
- Failed: {summary['failed_scenarios']}
- Skipped: {summary['skipped_scenarios']}
- Pass Rate: {round(summary['passed_scenarios']/max(summary['total_scenarios'],1)*100,1)}%
- Duration: {summary.get('execution_time_str','unknown')}

MODULE BREAKDOWN:
{json.dumps(summary['modules'], indent=2)}

FAILURES ({len(summary['failures'])} total):
{json.dumps(summary['failures'][:20], indent=2)}

Respond ONLY with a valid JSON object — no markdown, no explanation:
{{
  "overall_health": "Healthy|Degraded|Critical",
  "health_reason": "one sentence",
  "executive_summary": "2-3 sentences for a manager",
  "working_features": ["feature that works"],
  "broken_features": ["feature: what is broken"],
  "root_cause_patterns": ["pattern: N occurrences"],
  "improvements_needed": [
    {{"priority": "High|Medium|Low", "area": "area", "description": "what to fix"}}
  ],
  "test_quality_observations": ["observation"],
  "next_steps": ["actionable step"]
}}"""

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=payload,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return json.loads(data["content"][0]["text"])

    except Exception as e:
        print(f"[WARN] Claude API unavailable ({e}). Using static analysis.")
        return static_analysis(summary)


def static_analysis(summary: dict) -> dict:
    rate    = round(summary['passed_scenarios'] / max(summary['total_scenarios'], 1) * 100, 1)
    health  = "Healthy" if rate >= 80 else "Degraded" if rate >= 50 else "Critical"
    working = [m for m, v in summary['modules'].items() if v['failed'] == 0 and v['passed'] > 0]
    broken  = [m for m, v in summary['modules'].items() if v['failed'] > 0]
    counts  = {}
    for f in summary['failures']:
        err = f['error'].lower()
        k = ("TimeoutException — element not found" if "timeout" in err
             else "AssertionError — wrong expected value" if "assert" in err or "expected" in err
             else "Other error")
        counts[k] = counts.get(k, 0) + 1
    return {
        "overall_health": health,
        "health_reason": f"{rate}% pass rate across {summary['total_scenarios']} scenarios",
        "executive_summary": (
            f"The test suite ran {summary['total_scenarios']} scenarios and achieved a {rate}% pass rate "
            f"in {summary.get('execution_time_str','unknown')}. "
            f"{len(working)} module(s) are fully functional. "
            f"{len(broken)} module(s) have failures requiring attention before release."
        ),
        "working_features":  working or ["No fully passing modules detected"],
        "broken_features":   broken  or ["No failures detected"],
        "root_cause_patterns": [f"{k}: {v} occurrence(s)" for k, v in counts.items()] or ["No failures"],
        "improvements_needed": [
            {"priority": "High", "area": m,
             "description": f"{summary['modules'][m]['failed']} scenario(s) failing in {m}"}
            for m in broken
        ],
        "test_quality_observations": [
            "Login tests use placeholder credentials — real authentication will always fail",
            "Some Verify steps use AI-generated expected text that may not match the real site",
            "Soft assertions are used for known mismatches to avoid false failures",
        ],
        "next_steps": [
            "Open browser DevTools on failing pages and verify element IDs match the spec",
            "Update Verify steps with text that actually appears on calculator.net",
            "Replace test@example.com with real credentials or mock the login endpoint",
            "Run: gauge run specs --tags happy_path  to isolate core functionality",
        ],
    }


# ---------------------------------------------------------------------------
# HTML Generation
# ---------------------------------------------------------------------------

def generate_html(summary: dict, ai: dict) -> str:
    pass_rate    = round(summary['passed_scenarios'] / max(summary['total_scenarios'], 1) * 100, 1)
    health_color = {"Healthy": "#00d4a0", "Degraded": "#f59e0b", "Critical": "#ef4444"}.get(
        ai.get("overall_health", "Degraded"), "#f59e0b")

    module_labels = json.dumps(list(summary['modules'].keys()))
    module_passed = json.dumps([v['passed'] for v in summary['modules'].values()])
    module_failed = json.dumps([v['failed'] for v in summary['modules'].values()])

    rows = ""
    for spec in summary['specs']:
        for sc in spec['scenarios']:
            status = "skipped" if sc['skipped'] else ("failed" if sc['failed'] else "passed")
            badge  = {"passed":'<span class="badge pass">PASS</span>',
                      "failed":'<span class="badge fail">FAIL</span>',
                      "skipped":'<span class="badge skip">SKIP</span>'}[status]
            err_html = ""
            if sc['failed_steps']:
                err = sc['failed_steps'][0]['error'][:150].replace('<','&lt;').replace('>','&gt;')
                err_html = f'<div class="err-msg">{err}</div>'
            tags_html = "".join(f'<span class="tag">{t}</span>' for t in sc.get('tags', []))
            t_sec = f"{sc['execution_time']/1000:.1f}s" if sc['execution_time'] else "—"
            rows += (f'<tr class="row-{status}">'
                     f'<td>{badge}</td><td class="sc-name">{sc["name"]}</td>'
                     f'<td>{tags_html}</td><td>{t_sec}</td><td>{err_html}</td></tr>\n')

    imps = ""
    for imp in ai.get("improvements_needed", []):
        pri   = imp.get("priority", "Medium")
        color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(pri, "#6b7280")
        imps += (f'<div class="imp-card"><span class="pri" style="background:{color}">{pri}</span>'
                 f'<strong>{imp.get("area","")}</strong><p>{imp.get("description","")}</p></div>')

    def lis(items, icon="→"):
        return "".join(f'<li><span class="ico">{icon}</span>{i}</li>' for i in (items or []))

    exec_time = summary.get("execution_time_str") or _ms_to_str(summary["execution_time_ms"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Test Report — calculator.net</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<style>
:root{{--bg:#07080d;--s1:#0f1117;--s2:#161820;--border:#1f2130;--text:#dde1f0;--muted:#555a7a;
  --pass:#10e8a0;--fail:#ff3d6b;--skip:#4b5068;--warn:#fbbf24;--accent:#6c63ff;--health:{health_color};}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Space Grotesk',sans-serif;font-size:14px;line-height:1.6}}
body::before{{content:'';position:fixed;inset:0;z-index:-1;
  background-image:radial-gradient(ellipse 80% 50% at 50% -20%,rgba(108,99,255,.12),transparent);}}
header{{padding:36px 52px 28px;border-bottom:1px solid var(--border);background:linear-gradient(180deg,var(--s1),var(--bg));}}
.hrow{{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}}
.htitle h1{{font-size:26px;font-weight:700;letter-spacing:-.5px}}
.htitle p{{color:var(--muted);font-size:12px;font-family:'IBM Plex Mono',monospace;margin-top:5px}}
.hpill{{display:inline-flex;align-items:center;gap:9px;border:1px solid var(--health);border-radius:999px;
  padding:8px 18px;color:var(--health);font-weight:600;font-size:13px}}
.hdot{{width:8px;height:8px;border-radius:50%;background:var(--health);box-shadow:0 0 10px var(--health);animation:blink 2s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
.hreason{{color:var(--muted);font-size:11px;font-family:'IBM Plex Mono',monospace;margin-top:6px;text-align:right}}
main{{max-width:1360px;margin:0 auto;padding:44px 52px}}
.stats{{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin-bottom:44px}}
@media(max-width:1100px){{.stats{{grid-template-columns:repeat(3,1fr)}}}}
.sc{{background:var(--s1);border:1px solid var(--border);border-radius:14px;padding:22px 20px;position:relative;overflow:hidden;transition:border-color .2s}}
.sc:hover{{border-color:var(--accent)}}
.sc .v{{font-size:38px;font-weight:700;line-height:1;margin-bottom:5px;font-family:'IBM Plex Mono',monospace}}
.sc .l{{font-size:10px;text-transform:uppercase;letter-spacing:1.2px;color:var(--muted)}}
.sc.p .v{{color:var(--pass)}}.sc.f .v{{color:var(--fail)}}.sc.r .v{{color:var(--accent)}}.sc.k .v{{color:var(--skip)}}
.sc-glow{{position:absolute;bottom:-24px;right:-24px;width:90px;height:90px;border-radius:50%;opacity:.07}}
.sc.p .sc-glow{{background:var(--pass)}}.sc.f .sc-glow{{background:var(--fail)}}.sc.r .sc-glow{{background:var(--accent)}}
.esumm{{background:linear-gradient(135deg,rgba(108,99,255,.1),rgba(16,232,160,.06));border:1px solid rgba(108,99,255,.25);
  border-radius:14px;padding:24px 28px;margin-bottom:44px;font-size:15px;line-height:1.85}}
.esumm strong{{color:var(--accent)}}
.charts{{display:grid;grid-template-columns:2fr 1fr;gap:22px;margin-bottom:44px}}
.cc{{background:var(--s1);border:1px solid var(--border);border-radius:14px;padding:26px}}
.cc h3{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.4px;color:var(--muted);margin-bottom:22px;font-family:'IBM Plex Mono',monospace}}
.dw{{max-width:200px;margin:0 auto}}
.sec{{margin-bottom:44px}}
.sec-hdr{{display:flex;align-items:center;gap:12px;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--border)}}
.sec-hdr h2{{font-size:15px;font-weight:700;text-transform:uppercase;letter-spacing:.8px}}
.sec-num{{background:var(--accent);color:#fff;border-radius:5px;padding:2px 9px;font-size:11px;font-family:'IBM Plex Mono',monospace}}
.ai-grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:44px}}
.ai-card{{background:var(--s1);border:1px solid var(--border);border-radius:14px;padding:22px}}
.ai-card h3{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.4px;color:var(--muted);margin-bottom:14px;
  display:flex;align-items:center;gap:8px;font-family:'IBM Plex Mono',monospace}}
.ai-card ul{{list-style:none}}
.ai-card ul li{{padding:8px 0;border-bottom:1px solid var(--border);display:flex;gap:9px;font-size:13px;align-items:flex-start}}
.ai-card ul li:last-child{{border-bottom:none}}
.ico{{color:var(--accent);flex-shrink:0;margin-top:1px;font-weight:600}}
.imps{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-bottom:44px}}
.imp-card{{background:var(--s1);border:1px solid var(--border);border-radius:12px;padding:16px 18px;transition:border-color .2s}}
.imp-card:hover{{border-color:var(--warn)}}
.imp-card strong{{display:block;margin-bottom:5px;font-size:13px}}
.imp-card p{{font-size:12px;color:var(--muted);line-height:1.5}}
.pri{{display:inline-block;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;
  padding:2px 8px;border-radius:4px;color:#fff;margin-bottom:8px;font-family:'IBM Plex Mono',monospace}}
.twrap{{background:var(--s1);border:1px solid var(--border);border-radius:14px;overflow:hidden}}
.fbar{{display:flex;gap:8px;padding:14px 18px;border-bottom:1px solid var(--border);flex-wrap:wrap}}
.fb{{background:var(--s2);border:1px solid var(--border);color:var(--text);padding:5px 14px;border-radius:6px;
  cursor:pointer;font-size:12px;font-family:'IBM Plex Mono',monospace;transition:all .15s}}
.fb.active,.fb:hover{{background:var(--accent);border-color:var(--accent);color:#fff}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:11px 15px;font-size:10px;text-transform:uppercase;letter-spacing:1.2px;
  color:var(--muted);font-family:'IBM Plex Mono',monospace;background:var(--s2);border-bottom:1px solid var(--border)}}
td{{padding:11px 15px;border-bottom:1px solid rgba(31,33,48,.7);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
tr.row-failed{{background:rgba(255,61,107,.03)}}
tr.row-passed:hover{{background:rgba(16,232,160,.03)}}
tr.row-failed:hover{{background:rgba(255,61,107,.06)}}
.sc-name{{font-size:13px;max-width:380px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:4px;font-size:10px;font-weight:700;font-family:'IBM Plex Mono',monospace;letter-spacing:.5px}}
.badge.pass{{background:rgba(16,232,160,.15);color:var(--pass)}}
.badge.fail{{background:rgba(255,61,107,.15);color:var(--fail)}}
.badge.skip{{background:rgba(75,80,104,.2);color:var(--skip)}}
.tag{{display:inline-block;background:rgba(108,99,255,.15);color:var(--accent);border-radius:4px;
  padding:2px 7px;font-size:10px;margin:2px;font-family:'IBM Plex Mono',monospace}}
.err-msg{{font-family:'IBM Plex Mono',monospace;font-size:11px;color:var(--fail);background:rgba(255,61,107,.08);
  padding:6px 10px;border-radius:6px;margin-top:4px;max-width:420px;word-break:break-word;line-height:1.4}}
footer{{text-align:center;padding:28px;color:var(--muted);font-size:11px;border-top:1px solid var(--border);font-family:'IBM Plex Mono',monospace}}
</style>
</head>
<body>
<header>
  <div class="hrow">
    <div class="htitle">
      <h1>calculator.net — Test Report</h1>
      <p>Generated {summary['timestamp']} · Gauge + Selenium + Python</p>
    </div>
    <div>
      <div class="hpill"><div class="hdot"></div>{ai.get('overall_health','Unknown')}</div>
      <div class="hreason">{ai.get('health_reason','')}</div>
    </div>
  </div>
</header>
<main>

<div class="stats">
  <div class="sc"><div class="v">{summary['total_scenarios']}</div><div class="l">Total Scenarios</div><div class="sc-glow"></div></div>
  <div class="sc p"><div class="v">{summary['passed_scenarios']}</div><div class="l">Passed</div><div class="sc-glow"></div></div>
  <div class="sc f"><div class="v">{summary['failed_scenarios']}</div><div class="l">Failed</div><div class="sc-glow"></div></div>
  <div class="sc k"><div class="v">{summary['skipped_scenarios']}</div><div class="l">Skipped</div><div class="sc-glow"></div></div>
  <div class="sc r"><div class="v">{pass_rate}%</div><div class="l">Pass Rate</div><div class="sc-glow"></div></div>
  <div class="sc"><div class="v" style="font-size:22px">{exec_time}</div><div class="l">Duration</div></div>
</div>

<div class="esumm"><strong>Executive Summary — </strong>{ai.get('executive_summary','')}</div>

<div class="charts">
  <div class="cc"><h3>Pass / Fail by Module</h3><canvas id="moduleChart" height="200"></canvas></div>
  <div class="cc"><h3>Overall Result</h3><div class="dw"><canvas id="donutChart"></canvas></div></div>
</div>

<div class="sec">
  <div class="sec-hdr"><span class="sec-num">AI</span><h2>Analysis</h2></div>
  <div class="ai-grid">
    <div class="ai-card"><h3>✓ Working Features</h3><ul>{lis(ai.get('working_features',[]),'✓')}</ul></div>
    <div class="ai-card"><h3>✗ Broken / Failing</h3><ul>{lis(ai.get('broken_features',[]),'✗')}</ul></div>
    <div class="ai-card"><h3>⚠ Root Cause Patterns</h3><ul>{lis(ai.get('root_cause_patterns',[]),'→')}</ul></div>
    <div class="ai-card"><h3>→ Next Steps</h3><ul>{lis(ai.get('next_steps',[]),'→')}</ul></div>
  </div>
</div>

<div class="sec">
  <div class="sec-hdr"><span class="sec-num">{len(ai.get('improvements_needed',[]))}</span><h2>Improvements Needed</h2></div>
  <div class="imps">{imps}</div>
</div>

<div class="sec">
  <div class="sec-hdr"><span class="sec-num">{summary['total_scenarios']}</span><h2>All Scenarios</h2></div>
  <div class="twrap">
    <div class="fbar">
      <button class="fb active" onclick="ft('all',this)">All ({summary['total_scenarios']})</button>
      <button class="fb" onclick="ft('passed',this)">Passed ({summary['passed_scenarios']})</button>
      <button class="fb" onclick="ft('failed',this)">Failed ({summary['failed_scenarios']})</button>
      <button class="fb" onclick="ft('skipped',this)">Skipped ({summary['skipped_scenarios']})</button>
    </div>
    <table id="tbl">
      <thead><tr><th>Status</th><th>Scenario</th><th>Tags</th><th>Time</th><th>Error</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>

</main>
<footer>calculator.net Automated Test Report · {summary['timestamp']} · Gauge + Selenium + Claude AI</footer>
<script>
new Chart(document.getElementById('moduleChart'),{{type:'bar',data:{{labels:{module_labels},datasets:[
  {{label:'Passed',data:{module_passed},backgroundColor:'rgba(16,232,160,.75)',borderRadius:4}},
  {{label:'Failed',data:{module_failed},backgroundColor:'rgba(255,61,107,.75)',borderRadius:4}}
]}},options:{{responsive:true,maintainAspectRatio:false,
  plugins:{{legend:{{labels:{{color:'#dde1f0',font:{{size:11}}}}}}}},
  scales:{{x:{{ticks:{{color:'#555a7a',font:{{size:10}}}},grid:{{color:'rgba(31,33,48,.6)'}}}},
    y:{{ticks:{{color:'#555a7a',stepSize:1}},grid:{{color:'rgba(31,33,48,.6)'}}}}}}
}}}});
new Chart(document.getElementById('donutChart'),{{type:'doughnut',data:{{
  labels:['Passed','Failed','Skipped'],
  datasets:[{{data:[{summary['passed_scenarios']},{summary['failed_scenarios']},{summary['skipped_scenarios']}],
    backgroundColor:['rgba(16,232,160,.8)','rgba(255,61,107,.8)','rgba(75,80,104,.5)'],
    borderColor:['#10e8a0','#ff3d6b','#4b5068'],borderWidth:2,hoverOffset:6}}]
}},options:{{cutout:'72%',plugins:{{legend:{{position:'bottom',labels:{{color:'#dde1f0',padding:14,font:{{size:12}}}}}}}}}}
}});
function ft(f,btn){{document.querySelectorAll('.fb').forEach(b=>b.classList.remove('active'));btn.classList.add('active');
  document.querySelectorAll('#tbl tbody tr').forEach(r=>{{r.style.display=(f==='all'||r.classList.contains('row-'+f))?'':'none';}});}}
</script>
</body></html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate AI-powered test report")
    parser.add_argument("--from-output", "-f", metavar="FILE",
                        help="Saved gauge console output file (most reliable)")
    parser.add_argument("--results", "-r", metavar="FILE",
                        help="Specific result JSON/JS/HTML file")
    parser.add_argument("--output", "-o", default=None, metavar="FILE",
                        help="Output HTML path (default: reports/ai_report.html)")
    args = parser.parse_args()

    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent
    out_path     = Path(args.output) if args.output else project_root / "reports" / "ai_report.html"

    summary = None

    if args.from_output:
        p = Path(args.from_output)
        if not p.is_absolute():
            p = project_root / p
        print(f"[INFO] Parsing console output: {p}")
        summary = parse_console_output(p.read_text(encoding="utf-8", errors="ignore"))

    elif args.results:
        p = Path(args.results)
        if not p.is_absolute():
            p = project_root / p
        print(f"[INFO] Reading: {p}")
        if p.suffix == ".html" or p.name == "index.html":
            summary = parse_index_html(p)
        else:
            summary = _try_parse_file(p)

    else:
        print(f"[INFO] Auto-detecting results in: {project_root}")
        kind, path = find_result_source(project_root)
        if kind == "json":
            print(f"[INFO] Found: {path.relative_to(project_root)}")
            summary = _try_parse_file(path)
        elif kind == "html":
            print(f"[INFO] Found index.html, trying to extract data...")
            summary = parse_index_html(path)

    if not summary or summary['total_scenarios'] == 0:
        print("\n[ERROR] No test result data found.")
        print()
        print("  ── SOLUTION ─────────────────────────────────────────────")
        print("  Save gauge output to a file, then pass it to this script:")
        print()
        print("    gauge run specs 2>&1 | tee gauge_output.txt")
        print("    python gauge_builder/report_generator.py --from-output gauge_output.txt")
        print()
        print("  Then open:  reports\\ai_report.html")
        print("  ─────────────────────────────────────────────────────────")
        sys.exit(1)

    rate = round(summary['passed_scenarios'] / max(summary['total_scenarios'], 1) * 100, 1)
    print(f"[INFO] {summary['total_scenarios']} scenarios — "
          f"{summary['passed_scenarios']} passed, {summary['failed_scenarios']} failed ({rate}%)")
    print(f"[INFO] Duration: {summary.get('execution_time_str','—')}")
    print(f"[INFO] Modules: {', '.join(summary['modules'].keys())}")

    print("[INFO] Running AI analysis...")
    ai = analyze_with_claude(summary)
    print(f"[INFO] Health: {ai.get('overall_health')} — {ai.get('health_reason')}")

    print("[INFO] Generating HTML report...")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(generate_html(summary, ai), encoding="utf-8")
    print(f"\n[OK]  Report: {out_path}")
    print(f"      Run:    start \"{out_path}\"")


if __name__ == "__main__":
    main()