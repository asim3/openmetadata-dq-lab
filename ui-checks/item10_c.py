import re
from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/service/databaseServices/dqlab_oracle/agents")
    page.wait_for_timeout(4000)
    card = page.get_by_test_id("agent-card-dqlab_oracle.a8aeb513-432e-45bc-b371-74488e30cc7f")
    card.scroll_into_view_if_needed(); page.wait_for_timeout(500)
    print(" / ".join(card.inner_text().split()))
    card.get_by_test_id("more-actions").click()
    page.wait_for_timeout(500)
    shot(page, "i10_10_menu")
    for el in page.query_selector_all("[role=menuitem]"): print(el.inner_text())
    page.get_by_text("Edit configuration", exact=True).click()
    page.wait_for_timeout(3000)
    shot(page, "i10_11_edit")
    print(page.url)
    for el in page.query_selector_all("input,button,[role=switch]"):
        print(el.evaluate("e=>[e.tagName,e.type,e.id,e.getAttribute('data-testid'),e.innerText.slice(0,40)].join('|')"))
    b.close()
