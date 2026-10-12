from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_mysql/agents"); page.wait_for_timeout(5000)
    for c in page.locator("[data-testid^='agent-card-']").all():
        print(" ".join(c.inner_text().split()))
    t = " ".join(page.locator("body").inner_text().split())
    i = t.find("Agents deploying"); j = t.find("Deployment complete")
    print("banner:", t[i:i+160] if i>=0 else t[j:j+60])
    shot(page, "i03_1_agents")
    b.close()
