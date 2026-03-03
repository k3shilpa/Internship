"""Flask Web UI for AI Exploratory Tester."""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
(REPORTS_DIR / "screenshots").mkdir(exist_ok=True)


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

    @app.route("/")
    def index():
        return render_template("index.html", base_url=os.getenv("BASE_URL", ""))

    @app.route("/run", methods=["POST"])
    def run_tests():
        target_url = request.form.get("url", "").strip()
        if not target_url:
            return jsonify({"error": "No URL provided"}), 400

        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = f"{timestamp}_{run_id}"

        try:
            # 1. DOM Analysis
            from intelligence_layer.dom_analyzer import DOMAnalyzer
            analyzer = DOMAnalyzer(target_url)
            dom_data = analyzer.extract()

            # 2. RAG Context
            from intelligence_layer.rag_engine import RAGEngine
            rag = RAGEngine()
            context = rag.query(dom_data["summary"])

            # 3. AI Test Generation
            from intelligence_layer.testcase_generator import TestCaseGenerator
            generator = TestCaseGenerator()
            test_cases = generator.generate(dom_data, context)

            # 4. Persist to JSON store
            store_path = BASE_DIR / "intelligence_layer" / "json_store" / f"{report_id}.json"
            store_path.parent.mkdir(exist_ok=True)
            store_path.write_text(json.dumps({
                "report_id": report_id,
                "url": target_url,
                "timestamp": timestamp,
                "dom_data": dom_data,
                "test_cases": test_cases,
            }, indent=2))

            # 5. Gauge Execution
            from execution_layer.gauge_runner import GaugeRunner
            runner = GaugeRunner(report_id=report_id)
            runner.run(target_url, test_cases)

            return redirect(url_for("report", report_id=report_id))

        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/report/<report_id>")
    def report(report_id):
        store_path = BASE_DIR / "intelligence_layer" / "json_store" / f"{report_id}.json"
        if not store_path.exists():
            return "Report not found", 404

        data = json.loads(store_path.read_text())
        results_path = REPORTS_DIR / f"{report_id}_results.json"
        results = json.loads(results_path.read_text()) if results_path.exists() else {}
        screenshots = sorted((REPORTS_DIR / "screenshots").glob(f"{report_id}_*.png"))
        screenshot_names = [s.name for s in screenshots]

        return render_template(
            "report.html",
            report_id=report_id,
            data=data,
            results=results,
            screenshots=screenshot_names,
        )

    @app.route("/api/reports")
    def list_reports():
        store_dir = BASE_DIR / "intelligence_layer" / "json_store"
        reports = []
        if store_dir.exists():
            for f in sorted(store_dir.glob("*.json"), reverse=True)[:20]:
                try:
                    d = json.loads(f.read_text())
                    reports.append({
                        "report_id": d.get("report_id"),
                        "url": d.get("url"),
                        "timestamp": d.get("timestamp"),
                    })
                except Exception:
                    pass
        return jsonify(reports)

    return app