import sys
from playwright.sync_api import sync_playwright
from common import *
IDS = dict(a.split("=") for a in sys.argv[1:])
SVC = "dqlab_mysql"

def edit_url(kind): return f"{BASE}/service/databaseServices/{SVC}/edit-ingestion/{SVC}.{IDS[kind]}/{kind}"

def on_demand(page):
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(1500)
    page.get_by_text("On Demand", exact=True).click(); page.wait_for_timeout(500)
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(6000)

def delete_agent(page, kind):
    page.goto(f"{BASE}/service/databaseServices/{SVC}/agents"); page.wait_for_timeout(4500)
    card = page.get_by_test_id(f"agent-card-{SVC}.{IDS[kind]}")
    card.get_by_test_id("more-actions").click(); page.wait_for_timeout(500)
    page.get_by_text("Delete agent", exact=True).click(); page.wait_for_timeout(800)
    page.get_by_test_id("confirm-button").click(); page.wait_for_timeout(4000)

with sync_playwright() as p:
    b, page = open_page(p)
    # Metadata: On Demand
    page.goto(edit_url("metadata")); page.wait_for_timeout(3000); on_demand(page); print("metadata done")
    delete_agent(page, "lineage"); print("lineage deleted")
    delete_agent(page, "usage"); print("usage deleted")
    # AutoClassification
    page.goto(edit_url("autoClassification")); page.wait_for_timeout(3000)
    for t in ("ingestion-section-filters-toggle","ingestion-section-scope-toggle","ingestion-section-advanced-toggle"):
        page.get_by_test_id(t).click(); page.wait_for_timeout(300)
    for id_, want in (("root/storeSampleData", True), ("root/enableAutoClassification", False)):
        cb = page.locator(f"input[id='{id_}']")
        if cb.is_checked() != want:
            cb.evaluate("e=>e.closest('label').scrollIntoView({block:'center'})")
            page.locator(f"label:has(input[id='{id_}'])").click()
        print(id_, cb.is_checked())
    on_demand(page); print("autoclass done")
    # Profiler: classification filter
    page.goto(edit_url("profiler")); page.wait_for_timeout(3000)
    page.get_by_test_id("ingestion-section-filters-toggle").click(); page.wait_for_timeout(500)
    page.get_by_text("Classifications", exact=True).click(); page.wait_for_timeout(500)
    shot(page, "i03_2_profiler_filters_before")
    page.get_by_test_id("classificationFilterPattern-scan-all-button").click(); page.wait_for_timeout(500)
    on_demand(page); print("profiler done")
    b.close()
