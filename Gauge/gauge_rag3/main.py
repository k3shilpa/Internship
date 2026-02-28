"""
main.py - AI-Driven Automated Exploratory Testing Pipeline
==========================================================
Full pipeline orchestrator:
  URL → Crawler → RAG → Groq AI → Test Cases → Gauge Specs → Execution → Report

Usage:
  python main.py --url https://example.com
  python main.py --url https://shop.example.com --max-pages 5
  python main.py --metadata data/metadata/example.json   # Skip crawling
  python main.py --testcases data/testcases/example.json # Skip crawl+AI
  python main.py --build-rag                              # Just build knowledge base
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║      AI-Driven Automated Exploratory Testing Framework       ║
║      Gauge + Selenium + Groq AI + RAG                        ║
╚══════════════════════════════════════════════════════════════╝
    """)


def build_rag_knowledge_base():
    """Build/rebuild the RAG vector store from knowledge base files."""
    logger.info("\n📚 Building RAG Knowledge Base...")
    from rag.embedder import KnowledgeBaseEmbedder
    embedder = KnowledgeBaseEmbedder()
    count = embedder.embed_all()
    logger.info(f"✅ RAG Knowledge Base ready: {count} chunks indexed")
    return count


def run_crawler(url: str, max_pages: int) -> dict:
    """Phase 1: Crawl URL and extract element metadata."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 1: WEB CRAWLING")
    logger.info(f"{'='*60}")

    from crawler.web_crawler import WebCrawler
    crawler = WebCrawler(base_url=url, max_pages=max_pages)
    metadata = crawler.crawl()

    pages = len(metadata.get("pages", []))
    logger.info(f"✅ Crawling complete: {pages} pages processed")
    return metadata


def run_ai_generation(metadata: dict) -> dict:
    """Phase 2+3: Generate test cases using AI + RAG."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 2: AI TEST CASE GENERATION (Groq + RAG)")
    logger.info(f"{'='*60}")

    from ai_engine.test_generator import TestCaseGenerator
    generator = TestCaseGenerator()
    test_cases = generator.generate_from_metadata(metadata)

    total = test_cases.get("statistics", {}).get("total", 0)
    logger.info(f"✅ AI Generation complete: {total} test cases generated")
    return test_cases


def run_gauge_generation(testcases_data: dict, testcases_path: str) -> list:
    """Phase 4: Convert test cases to Gauge specs + stepimpl."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 3: GAUGE SPEC GENERATION")
    logger.info(f"{'='*60}")

    from gauge_generator.spec_generator import GaugeSpecGenerator
    from gauge_generator.step_impl_generator import StepImplGenerator

    spec_gen = GaugeSpecGenerator()
    spec_files = spec_gen.generate(testcases_path)

    step_gen = StepImplGenerator()
    step_impl_file = step_gen.generate(testcases_path)

    logger.info(f"✅ Gauge generation complete:")
    logger.info(f"   - {len(spec_files)} spec files")
    logger.info(f"   - step_impl.py generated")

    return spec_files


def run_execution(tags: str = None) -> dict:
    """Phase 5: Execute Gauge tests."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 4: TEST EXECUTION")
    logger.info(f"{'='*60}")

    from executor.gauge_runner import GaugeRunner
    runner = GaugeRunner()
    results = runner.run_all(tags=tags)

    summary = results.get("summary", {})
    logger.info(f"✅ Execution complete:")
    logger.info(f"   - Total: {summary.get('total_scenarios', 0)}")
    logger.info(f"   - Passed: {summary.get('passed', 0)}")
    logger.info(f"   - Failed: {summary.get('failed', 0)}")
    logger.info(f"   - Pass Rate: {summary.get('pass_rate', 0)}%")

    return results


def run_report(execution_results: dict, testcases_path: str, url: str) -> Path:
    """Phase 6: Generate HTML report."""
    logger.info(f"\n{'='*60}")
    logger.info(f"PHASE 5: REPORT GENERATION")
    logger.info(f"{'='*60}")

    from reports.report_generator import ReportGenerator
    execution_results["base_url"] = url
    report_gen = ReportGenerator()
    report_path = report_gen.generate(execution_results, testcases_path)

    logger.info(f"✅ Report generated: {report_path}")
    return report_path


def find_latest_file(directory: Path, pattern: str) -> str:
    """Find the most recently created file matching a pattern."""
    files = list(directory.glob(pattern))
    if not files:
        return None
    return str(max(files, key=lambda f: f.stat().st_mtime))


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="AI-Driven Automated Exploratory Testing Framework"
    )
    parser.add_argument("--url", type=str, help="URL to crawl and test")
    parser.add_argument("--max-pages", type=int, default=10, help="Max pages to crawl (default: 10)")
    parser.add_argument("--metadata", type=str, help="Path to existing metadata JSON (skip crawling)")
    parser.add_argument("--testcases", type=str, help="Path to existing testcases JSON (skip crawl+AI)")
    parser.add_argument("--build-rag", action="store_true", help="Build RAG knowledge base and exit")
    parser.add_argument("--skip-crawl", action="store_true", help="Skip crawling, use latest metadata")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI generation, use latest testcases")
    parser.add_argument("--skip-execute", action="store_true", help="Generate specs but don't execute")
    parser.add_argument("--tags", type=str, help="Gauge tags filter for execution (e.g., 'smoke')")
    parser.add_argument("--smoke-only", action="store_true", help="Run only high-priority smoke tests")

    args = parser.parse_args()

    # Import config paths
    from config import METADATA_DIR, TESTCASES_DIR

    # ── Special: Build RAG ──────────────────────────────────────────────────────
    if args.build_rag:
        build_rag_knowledge_base()
        return

    # ── Validate required args ──────────────────────────────────────────────────
    if not args.url and not args.metadata and not args.testcases and not args.skip_crawl:
        parser.print_help()
        logger.error("\n❌ Please provide --url, --metadata, or --testcases")
        sys.exit(1)

    # ── Always ensure RAG is built ──────────────────────────────────────────────
    try:
        from rag.vector_store import VectorStore
        vs = VectorStore()
        if not vs.is_ready():
            logger.info("🔧 RAG knowledge base not found. Building now...")
            build_rag_knowledge_base()
    except Exception as e:
        logger.warning(f"⚠️  Could not check RAG status: {e}. Building...")
        build_rag_knowledge_base()

    url = args.url or "https://unknown"
    metadata = None
    testcases_data = None
    testcases_path = args.testcases

    # ── Phase 1: Crawling ───────────────────────────────────────────────────────
    if args.testcases:
        logger.info(f"⏭️  Skipping crawl+AI, using testcases: {args.testcases}")
        with open(args.testcases) as f:
            testcases_data = json.load(f)
        url = testcases_data.get("generation_metadata", {}).get("base_url", url)

    elif args.metadata:
        logger.info(f"⏭️  Skipping crawl, using metadata: {args.metadata}")
        with open(args.metadata) as f:
            metadata = json.load(f)
        url = metadata.get("crawl_metadata", {}).get("base_url", url)

    elif args.skip_crawl:
        metadata_path = find_latest_file(METADATA_DIR, "*.json")
        if not metadata_path:
            logger.error("❌ No metadata files found. Run without --skip-crawl first.")
            sys.exit(1)
        logger.info(f"⏭️  Using latest metadata: {metadata_path}")
        with open(metadata_path) as f:
            metadata = json.load(f)
        url = metadata.get("crawl_metadata", {}).get("base_url", url)

    else:
        # Run the crawler
        metadata = run_crawler(args.url, args.max_pages)
        url = args.url

    # ── Phase 2: AI Test Generation ─────────────────────────────────────────────
    if not testcases_data:
        if args.skip_ai:
            testcases_path = find_latest_file(TESTCASES_DIR, "*.json")
            if not testcases_path:
                logger.error("❌ No testcase files found. Run without --skip-ai first.")
                sys.exit(1)
            logger.info(f"⏭️  Using latest testcases: {testcases_path}")
            with open(testcases_path) as f:
                testcases_data = json.load(f)
        else:
            testcases_data = run_ai_generation(metadata)
            # Find the file that was just saved
            testcases_path = find_latest_file(TESTCASES_DIR, "*.json")

    # ── Phase 3: Gauge Generation ───────────────────────────────────────────────
    if not testcases_path:
        testcases_path = find_latest_file(TESTCASES_DIR, "*.json")

    spec_files = run_gauge_generation(testcases_data, testcases_path)

    # ── Phase 4: Execution ──────────────────────────────────────────────────────
    if args.skip_execute:
        logger.info("\n⏭️  Skipping execution (--skip-execute flag set)")
        logger.info(f"   Specs are ready in gauge_project/specs/")
        logger.info(f"   Run manually: cd gauge_project && gauge run specs/")
        return

    tags = args.tags
    if args.smoke_only:
        tags = "smoke"

    execution_results = run_execution(tags=tags)

    # ── Phase 5: Report ─────────────────────────────────────────────────────────
    report_path = run_report(execution_results, testcases_path, url)

    # ── Final Summary ────────────────────────────────────────────────────────────
    summary = execution_results.get("summary", {})
    logger.info(f"""
{'='*60}
PIPELINE COMPLETE
{'='*60}
URL Tested:      {url}
Test Cases:      {testcases_data.get('statistics', {}).get('total', 0)} generated
Scenarios Run:   {summary.get('total_scenarios', 0)}
Passed:          {summary.get('passed', 0)} ✅
Failed:          {summary.get('failed', 0)} ❌
Pass Rate:       {summary.get('pass_rate', 0)}%
Report:          {report_path}
{'='*60}
    """)


if __name__ == "__main__":
    main()
