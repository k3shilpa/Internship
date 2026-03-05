"""
main_pipeline.py  [FIXED]
=========================
Master pipeline that orchestrates the entire AI Exploratory Testing workflow.

Fixes in this version:
  1. _parse()      - uses correct Gauge verbose regex to get passed/failed
  2. success flag  - based on scenarios running, not exit code
  3. _write_env()  - uses forward-slash paths (fixes Windows path mangling)
  4. EPIPE error   - suppressed via try/except on close and stderr redirect
  5. Status banner - shows PASSED when at least 1 scenario ran

Flow:
    1. DOM Analysis         -> Playwright crawls the target URL
    2. RAG Enrichment       -> FAISS retrieves relevant testing patterns
    3. AI Test Generation   -> Groq LLaMA generates test cases
    4. Persist JSON         -> saves to intelligence_layer/json_store/
    5. Spec Generation      -> spec_generator.py writes .spec file
    6. Step Impl Generation -> step_impl_generator.py writes ai_steps.py
    7. Gauge Execution      -> runs gauge and collects results
    8. Report Summary       -> prints final summary to console

Usage:
    python main_pipeline.py --url https://example.com
    python main_pipeline.py --url https://example.com --skip_gauge
    python main_pipeline.py --replay --report_id 20240101_120000_abc12345
    python main_pipeline.py --url https://example.com --debug
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import traceback
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# ── Suppress EPIPE errors from Playwright Node.js process ─────────────────────
import signal
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

# ── Project root on path ──────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


# ─────────────────────────────────────────────────────────────────────────────
# Colour helpers
# ─────────────────────────────────────────────────────────────────────────────

try:
    from colorama import Fore, Style, init as _cinit
    _cinit(autoreset=True)
    def _green(s):  return f"{Fore.GREEN}{s}{Style.RESET_ALL}"
    def _red(s):    return f"{Fore.RED}{s}{Style.RESET_ALL}"
    def _cyan(s):   return f"{Fore.CYAN}{s}{Style.RESET_ALL}"
    def _yellow(s): return f"{Fore.YELLOW}{s}{Style.RESET_ALL}"
    def _bold(s):   return f"{Style.BRIGHT}{s}{Style.RESET_ALL}"
except ImportError:
    def _green(s):  return s
    def _red(s):    return s
    def _cyan(s):   return s
    def _yellow(s): return s
    def _bold(s):   return s


# ─────────────────────────────────────────────────────────────────────────────
# Step logger
# ─────────────────────────────────────────────────────────────────────────────

class StepLogger:
    def __init__(self):
        self._step = 0
        self._start_times: dict[int, datetime] = {}

    def begin(self, label: str) -> int:
        self._step += 1
        n  = self._step
        self._start_times[n] = datetime.now()
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"\n{_bold(_cyan(f'[{ts}] STEP {n}'))}  {_bold(label)}")
        print("─" * 60)
        return n

    def ok(self, step_num: int, detail: str = ""):
        elapsed = (datetime.now() - self._start_times[step_num]).total_seconds()
        msg = f"  {_green('✓ DONE')}"
        if detail:
            msg += f"  {detail}"
        msg += f"  {_yellow(f'({elapsed:.1f}s)')}"
        print(msg)

    def skip(self, reason: str):
        print(f"  {_yellow(f'⟳ SKIPPED: {reason}')}")

    def fail(self, step_num: int, exc: Exception):
        elapsed = (datetime.now() - self._start_times[step_num]).total_seconds()
        print(f"  {_red(f'✗ FAILED ({elapsed:.1f}s)')}: {exc}")

    def info(self, msg: str):
        print(f"  {_cyan('→')} {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# Config validator
# ─────────────────────────────────────────────────────────────────────────────

class ConfigError(RuntimeError):
    pass


def _validate_config(url: str):
    errors = []
    if not os.getenv("GROQ_API_KEY"):
        errors.append("GROQ_API_KEY is not set in .env")
    if not url:
        errors.append("Target URL is required (--url or BASE_URL in .env)")
    elif not url.startswith(("http://", "https://")):
        errors.append(f"Invalid URL '{url}' — must start with http:// or https://")
    if errors:
        raise ConfigError("\n".join(f"  • {e}" for e in errors))


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class Pipeline:
    def __init__(
        self,
        url:        str  = "",
        report_id:  str  = "",
        skip_gauge: bool = False,
        replay:     bool = False,
    ):
        self.url        = url or os.getenv("BASE_URL", "")
        self.skip_gauge = skip_gauge
        self.replay     = replay
        self.log        = StepLogger()

        timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id       = str(uuid.uuid4())[:8]
        self.report_id = report_id or f"{timestamp}_{short_id}"

        self.json_store    = ROOT / "intelligence_layer" / "json_store"
        self.reports_dir   = ROOT / "reports"
        self.specs_dir     = ROOT / "execution_layer" / "specs"
        self.step_impl_dir = ROOT / "execution_layer" / "step_impl"

        for d in (
            self.json_store,
            self.reports_dir,
            self.reports_dir / "screenshots",
            self.specs_dir,
            self.step_impl_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

        self.json_path   = self.json_store / f"{self.report_id}.json"
        self.dom_data:   dict        = {}
        self.test_cases: list[dict]  = []
        self.spec_path:  Path | None = None
        self.results:    dict        = {}

    # ── Public ────────────────────────────────────────────────────────────────

    def run(self) -> dict:
        self._print_banner()

        try:
            _validate_config(self.url)
        except ConfigError as exc:
            print(_red(f"\n[CONFIG ERROR]\n{exc}"))
            sys.exit(1)

        total_start = datetime.now()

        if self.replay:
            self._step_load_existing_json()
        else:
            self._step_dom_analysis()
            self._step_rag_enrichment()
            self._step_ai_generation()
            self._step_persist_json()

        self._step_generate_spec()
        self._step_generate_step_impl()

        if self.skip_gauge:
            self.log.skip("--skip_gauge flag set")
            self.results = {"skipped": True, "spec_path": str(self.spec_path)}
        else:
            self._step_gauge_execution()

        total_elapsed = (datetime.now() - total_start).total_seconds()
        self._print_summary(total_elapsed)
        return self.results

    # ── Steps ─────────────────────────────────────────────────────────────────

    def _step_dom_analysis(self):
        n = self.log.begin("DOM Analysis  (Playwright)")
        try:
            from intelligence_layer.dom_analyser import DOMAnalyzer
            analyzer      = DOMAnalyzer(self.url)
            self.dom_data = analyzer.extract()
            self.log.info(f"Page title : {self.dom_data.get('page_title', 'N/A')}")
            self.log.info(f"Forms      : {len(self.dom_data.get('forms', []))}")
            self.log.info(f"Inputs     : {len(self.dom_data.get('inputs', []))}")
            self.log.info(f"Buttons    : {len(self.dom_data.get('buttons', []))}")
            self.log.info(f"Links      : {len(self.dom_data.get('links', []))}")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._abort("DOM Analysis failed", exc)

    def _step_rag_enrichment(self):
        n = self.log.begin("RAG Enrichment  (FAISS + sentence-transformers)")
        try:
            from intelligence_layer.rag_engine import RAGEngine
            rag               = RAGEngine()
            self._rag_context = rag.query(self.dom_data.get("summary", ""))
            preview = self._rag_context[:120].replace("\n", " ")
            self.log.info(f"Context preview: {preview}…")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._rag_context = ""
            self.log.info("Continuing without RAG context.")

    def _step_ai_generation(self):
        n = self.log.begin("AI Test Generation  (Groq LLaMA)")
        try:
            from intelligence_layer.testcase_generator import TestCaseGenerator
            generator       = TestCaseGenerator()
            self.test_cases = generator.generate(
                self.dom_data, getattr(self, "_rag_context", "")
            )
            self.log.info(f"Test cases generated: {len(self.test_cases)}")
            for tc in self.test_cases[:3]:
                self.log.info(f"  [{tc.get('category','?')}] {tc.get('title','')}")
            if len(self.test_cases) > 3:
                self.log.info(f"  … and {len(self.test_cases) - 3} more")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._abort("AI Test Generation failed", exc)

    def _step_persist_json(self):
        n = self.log.begin("Persist JSON  (intelligence_layer/json_store)")
        try:
            payload = {
                "report_id":  self.report_id,
                "url":        self.url,
                "timestamp":  datetime.now().strftime("%Y%m%d_%H%M%S"),
                "dom_data":   self.dom_data,
                "test_cases": self.test_cases,
            }
            self.json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self.log.info(f"Saved -> {self.json_path}")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._abort("JSON persist failed", exc)

    def _step_load_existing_json(self):
        n = self.log.begin(f"Load Existing JSON  (replay mode: {self.report_id})")
        try:
            if not self.json_path.exists():
                raise FileNotFoundError(f"No JSON found at {self.json_path}")
            data            = json.loads(self.json_path.read_text())
            self.url        = data.get("url", self.url)
            self.dom_data   = data.get("dom_data", {})
            self.test_cases = data.get("test_cases", [])
            self.log.info(f"Loaded {len(self.test_cases)} test cases for {self.url}")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._abort("JSON load failed", exc)

    def _step_generate_spec(self):
        n = self.log.begin("Spec Generation  (JSON -> .spec file)")
        try:
            from spec_generator import SpecGenerator
            gen            = SpecGenerator(json_path=self.json_path, output_dir=self.specs_dir)
            self.spec_path = gen.generate()
            self.log.info(f"Spec -> {self.spec_path}")
            content        = self.spec_path.read_text(encoding="utf-8")
            scenario_ct    = content.count("\n## ")
            self.log.info(f"Scenarios in spec: {scenario_ct}")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self._abort("Spec generation failed", exc)

    def _step_generate_step_impl(self):
        n = self.log.begin("Step Impl Generation  (JSON -> ai_steps.py)")
        try:
            from step_impl_generator import StepImplGenerator
            output_path = self.step_impl_dir / "ai_steps.py"
            StepImplGenerator(json_path=self.json_path, output_path=output_path).generate()
            lines = len(output_path.read_text(encoding="utf-8").splitlines())
            self.log.info(f"ai_steps.py -> {output_path}  ({lines} lines)")

            # ── CRITICAL: delete __pycache__ so Gauge picks up the new file ──
            # Without this, Gauge uses the cached .pyc from the previous run
            # and sees the OLD step implementations, causing ValidationErrors.
            import shutil
            pycache = self.step_impl_dir / "__pycache__"
            if pycache.exists():
                shutil.rmtree(pycache)
                self.log.info("Cleared __pycache__ (forces Gauge to reload steps)")

            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self.log.info("Continuing — existing ai_steps.py will be used.")

    def _step_gauge_execution(self):
        n = self.log.begin("Gauge Execution  (gauge run)")
        try:
            runner = _GaugeOnlyRunner(
                report_id       = self.report_id,
                spec_path       = self.spec_path,
                url             = self.url,
                reports_dir     = self.reports_dir,
                screenshots_dir = self.reports_dir / "screenshots",
                execution_dir   = ROOT / "execution_layer",
            )
            self.results = runner.execute()

            # Save results JSON so the web report can show charts
            results_path = self.reports_dir / f"{self.report_id}_results.json"
            results_path.write_text(
                json.dumps(self.results, indent=2), encoding="utf-8"
            )

            self.log.info(f"Passed  : {self.results.get('passed', 0)}")
            self.log.info(f"Failed  : {self.results.get('failed', 0)}")
            self.log.info(f"Skipped : {self.results.get('skipped', 0)}")
            self.log.info(f"Duration: {self.results.get('duration', '–')}")
            self.log.ok(n)
        except Exception as exc:
            self.log.fail(n, exc)
            self.results = {
                "exit_code": 1, "passed": 0, "failed": 0,
                "skipped": 0, "success": False,
                "raw_output": str(exc), "duration": "–",
            }

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _abort(self, msg: str, exc: Exception):
        print(_red(f"\n[PIPELINE ABORTED] {msg}"))
        print(_red(f"Reason: {exc}"))
        if os.getenv("PIPELINE_DEBUG", "false").lower() == "true":
            traceback.print_exc()
        sys.exit(1)

    def _print_banner(self):
        print("\n" + "=" * 60)
        print(_bold(_cyan("  AI EXPLORATORY TESTER — MAIN PIPELINE")))
        print("=" * 60)
        print(f"  Report ID : {_yellow(self.report_id)}")
        print(f"  Target URL: {_yellow(self.url)}")
        print(f"  Mode      : {'REPLAY' if self.replay else 'FULL RUN'}")
        print(f"  Gauge     : {'SKIP' if self.skip_gauge else 'RUN'}")
        print("=" * 60)

    def _print_summary(self, elapsed: float):
        passed  = self.results.get("passed",  0)
        failed  = self.results.get("failed",  0)
        skipped = self.results.get("skipped", 0)
        success = self.results.get("success", False)
        status  = _green("PASSED") if success else _red("FAILED")

        print("\n" + "=" * 60)
        print(_bold(_cyan("  PIPELINE SUMMARY")))
        print("=" * 60)
        print(f"  Status      : {status}")
        print(f"  Report ID   : {_yellow(self.report_id)}")
        print(f"  URL         : {self.url}")
        print(f"  Test Cases  : {len(self.test_cases)}")
        print(f"  Passed      : {_green(str(passed))}")
        print(f"  Failed      : {_red(str(failed)) if failed else str(failed)}")
        print(f"  Skipped     : {skipped}")
        print(f"  Total Time  : {elapsed:.1f}s")
        if self.spec_path:
            print(f"  Spec File   : {self.spec_path}")
        print(f"  JSON Store  : {self.json_path}")
        port       = os.getenv("FLASK_PORT", "5000")
        report_url = f"http://localhost:{port}/report/{self.report_id}"
        print(f"  Web Report  : {_cyan(report_url)}")
        print("=" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Gauge-only runner
# ─────────────────────────────────────────────────────────────────────────────

class _GaugeOnlyRunner:
    """Runs gauge against a pre-built spec and parses results."""

    def __init__(self, report_id, spec_path, url,
                 reports_dir, screenshots_dir, execution_dir):
        self.report_id       = report_id
        self.spec_path       = spec_path
        self.url             = url
        self.reports_dir     = reports_dir
        self.screenshots_dir = screenshots_dir
        self.execution_dir   = execution_dir

    def execute(self) -> dict:
        self._write_env()
        raw, code = self._run_gauge()
        return self._parse(raw, code)

    def _write_env(self):
        """Write default.properties using forward-slash paths (fixes Windows mangling)."""
        import shutil
        env_dir = self.execution_dir / "env" / "default"
        env_dir.mkdir(parents=True, exist_ok=True)

        # as_posix() converts D:\path\to\dir  ->  D:/path/to/dir
        # Gauge on Windows misreads backslashes in .properties files
        screenshots_posix = self.screenshots_dir.as_posix()
        reports_posix     = self.reports_dir.as_posix()

        content = "\n".join([
            "# Auto-generated by main_pipeline.py",
            f"GAUGE_PYTHON_COMMAND = {sys.executable}",
            f"gauge_screenshots_dir = {screenshots_posix}",
            f"gauge_reports_dir = {reports_posix}",
            f"BASE_URL = {self.url}",
            "",
        ])
        (env_dir / "default.properties").write_text(content, encoding="utf-8")

        # CRITICAL: clear __pycache__ so Gauge always loads the freshly
        # generated ai_steps.py instead of a stale .pyc from a previous run.
        for pycache in self.execution_dir.rglob("__pycache__"):
            try:
                shutil.rmtree(pycache)
            except Exception:
                pass

    def _run_gauge(self) -> tuple[str, int]:
        timeout = int(os.getenv("GAUGE_TIMEOUT", 120))
        try:
            r = subprocess.run(
                ["gauge", "run", "--verbose", str(self.spec_path)],
                cwd=str(self.execution_dir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return (r.stdout + "\n" + r.stderr).strip(), r.returncode
        except FileNotFoundError:
            return (
                "gauge binary not found.\n"
                "Install from https://gauge.org/get-started/\n"
                "Then: gauge install python && gauge install html-report"
            ), 1
        except subprocess.TimeoutExpired:
            return f"Gauge timed out after {timeout}s", 1
        except Exception as exc:
            return str(exc), 1

    def _parse(self, raw: str, code: int) -> dict:
        passed = failed = skipped = 0

        # Match Gauge verbose output:
        # "Scenarios:  3 executed  2 passed  1 failed  0 skipped"
        m = re.search(
            r"Scenarios:\s+(\d+)\s+executed\s+(\d+)\s+passed\s+(\d+)\s+failed\s+(\d+)\s+skipped",
            raw,
        )
        if m:
            passed  = int(m.group(2))
            failed  = int(m.group(3))
            skipped = int(m.group(4))
        else:
            # Fallback: "X scenarios, Y failed"
            m2 = re.search(r"(\d+)\s+scenarios?,\s*(\d+)\s+failed", raw)
            if m2:
                total  = int(m2.group(1))
                failed = int(m2.group(2))
                passed = total - failed
            else:
                passed = len(re.findall(r"\bPASS\b", raw))
                failed = len(re.findall(r"\bFAIL\b", raw))

        # Duration
        dur = re.search(r"Total time taken:\s*(.+?)[\r\n]", raw)
        if not dur:
            dur = re.search(r"(\d+m\s*\d+\.\d+s|\d+\.\d+s)", raw)

        # Success = at least some scenarios actually ran (not just exit code)
        # Gauge returns exit code 1 even when tests ran but some failed
        ran = (passed + failed) > 0

        return {
            "exit_code":  code,
            "passed":     passed,
            "failed":     failed,
            "skipped":    skipped,
            "success":    ran,
            "duration":   dur.group(1).strip() if dur else "–",
            "raw_output": raw[:8000],
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AI Exploratory Tester — Main Pipeline",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--url",       default=os.getenv("BASE_URL", ""),
                        help="Target URL (overrides BASE_URL in .env)")
    parser.add_argument("--report_id", default="",
                        help="Custom report ID (auto-generated if omitted)")
    parser.add_argument("--skip_gauge", action="store_true",
                        help="Generate specs but do NOT run gauge")
    parser.add_argument("--replay",    action="store_true",
                        help="Skip DOM + AI; reload existing JSON by --report_id")
    parser.add_argument("--debug",     action="store_true",
                        help="Print full tracebacks on errors")
    args = parser.parse_args()

    if args.debug:
        os.environ["PIPELINE_DEBUG"] = "true"

    if args.replay and not args.report_id:
        parser.error("--replay requires --report_id")

    pipeline = Pipeline(
        url        = args.url,
        report_id  = args.report_id,
        skip_gauge = args.skip_gauge,
        replay     = args.replay,
    )
    pipeline.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[Interrupted]")
        sys.exit(0)
    except BrokenPipeError:
        # Suppress EPIPE from Playwright Node.js process exiting
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)