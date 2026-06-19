from __future__ import annotations

from pathlib import Path

from pipeline import generate_fast_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    input_path = generate_fast_report.INPUT_PATH
    latest_output_path = generate_fast_report.LATEST_OUTPUT_PATH

    if not input_path.is_file():
        print(f"ERROR: Fast Evidence Pack not found: {input_path.relative_to(PROJECT_ROOT).as_posix()}")
        print("Run the evidence pack build step first, or provide data/evidence/fast_evidence_pack_latest.json.")
        return 1

    report, item_count, news_count, announcement_count, report_count, success, errors = generate_fast_report.build_report()
    today = generate_fast_report.now_local().strftime("%Y%m%d")
    dated_output_path = PROJECT_ROOT / "reports" / f"fast_report_{today}.md"

    generate_fast_report.write_text(dated_output_path, report)
    generate_fast_report.write_text(latest_output_path, report)

    print("Offline report generation completed.")
    print(f"Input: {input_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Success: {success}")
    print(f"News item count: {news_count}")
    print(f"Announcement item count: {announcement_count}")
    print(f"Research report item count: {report_count}")
    print(f"Total evidence item count: {item_count}")
    print(f"Latest report: {latest_output_path.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Dated report: {dated_output_path.relative_to(PROJECT_ROOT).as_posix()}")

    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
