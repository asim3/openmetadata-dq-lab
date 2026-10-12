from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_oracle/agents")
    page.wait_for_timeout(4000)
    shot(page, "i10_9_agents")
    for el in page.query_selector_all("[data-testid]"):
        t = el.get_attribute("data-testid")
        if any(k in t.lower() for k in ("agent","pipeline","run","more","menu","edit","delete","tab")): print(t)
    b.close()
