from playwright.sync_api import sync_playwright
from common import *
AG = {"metadata":"69b2b8bc-b52f-4b5c-9546-31e0d1a347ed","lineage":"307582ea-5b6f-4518-ab21-550079a5fe75","autoClassification":"f4eddccb-27d2-44ca-b511-39d799cdf809"}
with sync_playwright() as p:
    b, page = open_page(p)
    for kind, pid in AG.items():
        page.goto(f"{BASE}/service/databaseServices/dqlab_oracle/edit-ingestion/dqlab_oracle.{pid}/{kind}")
        page.wait_for_timeout(3000)
        page.get_by_test_id("next-button").click(); page.wait_for_timeout(1500)
        page.get_by_text("On Demand", exact=True).click(); page.wait_for_timeout(500)
        page.get_by_test_id("next-button").click(); page.wait_for_timeout(6000)
        shot(page, f"i10_15_{kind}")
        print(kind, "submitted")
    b.close()
