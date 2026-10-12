import sys
from playwright.sync_api import sync_playwright
from common import *
IDS = {"autoClassification":"f4eddccb-27d2-44ca-b511-39d799cdf809","profiler":"a8aeb513-432e-45bc-b371-74488e30cc7f"}
kind = sys.argv[1]
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_oracle/agents"); page.wait_for_timeout(4000)
    card = page.get_by_test_id("agent-card-dqlab_oracle." + IDS[kind])
    print(" ".join(card.inner_text().split()))
    card.get_by_test_id("run-agent-button").click(); page.wait_for_timeout(3000)
    shot(page, f"i10_17_run_{kind}")
    b.close()
