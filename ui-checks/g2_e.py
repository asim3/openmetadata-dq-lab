from playwright.sync_api import sync_playwright
from common import *
LINKS = [("dqlab_mysql.default.dqlab.customers","Customer"),("dqlab_mysql.default.dqlab.orders","Order"),("dqlab_mysql.default.dqlab.products","Product"),("dqlab_oracle.default.dqlab.EMPLOYEES","Employee")]
with sync_playwright() as p:
    b, page = open_page(p)
    for fqn, term in LINKS:
        page.goto(f"{BASE}/table/{fqn}"); page.wait_for_timeout(3500)
        page.get_by_text("Glossary Term", exact=True).first.locator("xpath=following::button[1]").click(); page.wait_for_timeout(3000)
        page.keyboard.type(term); page.wait_for_timeout(2500)
        page.get_by_text(term, exact=True).last.click(); page.wait_for_timeout(500)
        page.get_by_test_id("saveAssociatedTag").click(); page.wait_for_timeout(2500)
        print("linked", term, "->", fqn.split(".")[-1])
    b.close()
