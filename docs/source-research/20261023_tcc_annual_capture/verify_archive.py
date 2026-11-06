"""Offline source-archive integrity check; no product imports or calculations."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
PDF_SHA = "7406e30d1f02f083611f594459b952494816d87237bf2203734ce6afb487155d"
URL = "https://media.taiwancement.com/web_tcc/comm/pdf/Annual_Report/114%E5%B9%B4%E5%BA%A6%E5%B9%B4%E5%A0%B1%E5%8F%8A%E5%B9%B4%E5%A0%B1%E9%99%84%E5%86%8A.pdf"


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def main():
    pdf = (ROOT / "raw/tcc-annual-114.response").read_bytes()
    assert len(pdf) == 4932379 and hashlib.sha256(pdf).hexdigest() == PDF_SHA
    assert pdf.startswith(b"%PDF-")
    assert hashlib.sha1(b"blob " + str(len(pdf)).encode() + b"\0" + pdf).hexdigest() == "f6d87f6ee476c56cb596a4d6fa326d8a45ac85ba"
    meta = load("raw/tcc-annual-114.meta.json")
    assert meta["url"] == URL and meta["http"] == 200
    assert meta["attempts"] == 1 and meta["retries"] == 0
    assert meta["redirects_followed"] is False
    assert meta["bytes"] == len(pdf) and meta["sha256"] == PDF_SHA
    assert meta["announced_at"] is None and meta["actual_effective_at"] is None
    assert not any(k.lower() in {"set-cookie", "set-cookie2", "authorization", "proxy-authorization"} for k in meta["headers"])
    processing = load("pdf-processing.json")
    assert processing["page_count"] == 113 and processing["formfeed_count"] == 113
    assert sha("raw/tcc-annual-114.txt") == processing["full_text_sha256"]
    for command in processing["commands"] + processing["renders"]:
        assert command["returncode"] == 0
        assert sha(command["stderr_file"]) == command["stderr_sha256"]
        assert (ROOT / command["stderr_file"]).stat().st_size == command["stderr_bytes"]
    visual = load("visual-review.json")
    assert visual["whole_book_visually_reviewed"] is False
    assert [p["physical_page"] for p in visual["pages"]] == [52, 57, 58, 60]
    for page in visual["pages"]:
        assert page["review_status"] == "MANUAL_VISUAL_REVIEWED_THIS_CODEX"
        assert sha(page["image"]) == page["image_sha256"]
        assert sha(page["native_text"]) == page["native_text_sha256"]
    observations = load("observations.json")
    assert observations["source_sha256"] == PDF_SHA
    assert observations["issuer_code"] == "1101"
    assert observations["announced_at"] is None and observations["actual_effective_at"] is None
    assert observations["formal_catalog_created"] is False
    assert observations["new_ledger_events"] == observations["independent_market_samples_added"] == 0
    assert observations["source_date_difference"]["reconciled"] is False
    assert observations["source_date_difference"]["actual_effective_at"] is None
    assert observations["qualification"] == "COMPANY_REPORTED_SOURCE_INVENTORY_NOT_LEDGER"
    for item in observations["observations"]:
        assert item["source_sha256"] == PDF_SHA
        assert item["actual_effective_at"] is None
        assert item["source_id"] == meta["source_id"]
    assert observations["execution_qualified"] is False
    assert observations["historical_signal_eligible"] is False
    assert observations["policy_authorized"] is False
    assert observations["imputed_close"] is observations["valuation"] is observations["primary_pressure_id"] is None
    print(json.dumps({"status": "PASS", "scope": "OFFLINE_SOURCE_ARCHIVE_INTEGRITY_NOT_PRODUCT_TESTS", "source_bytes": len(pdf), "source_sha256": PDF_SHA, "visually_reviewed_physical_pages": [52, 57, 58, 60], "source_warnings_preserved": True, "product_tests_run": 0}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
