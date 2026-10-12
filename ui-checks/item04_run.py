import sys
from playwright.sync_api import sync_playwright
from common import *
IDS = {"autoClassification":"c63fc07d-b98e-4d60-a271-a32574d517cd","profiler":"5a32b09f-5b3f-44ab-b847-5e159853abfc"}
kind = sys.argv[1]
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_mysql/agents"); page.wait_for_timeout(4000)
    card = page.get_by_test_id("agent-card-dqlab_mysql." + IDS[kind])
    print(" ".join(card.inner_text().split()))
    card.get_by_test_id("run-agent-button").click(); page.wait_for_timeout(3000)
    shot(page, f"i04_run_{kind}")
    b.close()
