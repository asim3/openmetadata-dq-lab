from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_oracle/agents"); page.wait_for_timeout(4000)
    card = page.get_by_test_id("agent-card-dqlab_oracle.56b0e701-a424-496d-91c3-e4fe410addf1")
    print(" ".join(card.inner_text().split()))
    card.get_by_test_id("more-actions").click(); page.wait_for_timeout(500)
    page.get_by_text("Delete agent", exact=True).click(); page.wait_for_timeout(1000)
    page.get_by_test_id("confirm-button").click(); page.wait_for_timeout(4000); shot(page, "i10_16_deleted")
    for el in page.query_selector_all("[role=dialog] button, [role=dialog] input, [role=dialog]"):
        print(el.evaluate("e=>[e.tagName,e.type,e.getAttribute('data-testid'),e.innerText.slice(0,80)].join('|')"))
    b.close()
