from playwright.sync_api import sync_playwright
from common import *
AC = BASE + "/service/databaseServices/dqlab_oracle/edit-ingestion/dqlab_oracle.f4eddccb-27d2-44ca-b511-39d799cdf809/autoClassification"
PF = BASE + "/service/databaseServices/dqlab_oracle/edit-ingestion/dqlab_oracle.a8aeb513-432e-45bc-b371-74488e30cc7f/profiler"
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(PF); page.wait_for_timeout(3000)
    page.get_by_test_id("ingestion-section-filters-toggle").click(); page.wait_for_timeout(500)
    page.get_by_text("Classifications", exact=True).click(); page.wait_for_timeout(500)
    page.get_by_test_id("classificationFilterPattern-scan-all-button").click(); page.wait_for_timeout(500)
    shot(page, "i10_19_pf_filters")
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(1500)
    page.get_by_text("On Demand", exact=True).click(); page.wait_for_timeout(500)
    page.get_by_test_id("next-button").click(); page.wait_for_timeout(6000)
    b.close()
