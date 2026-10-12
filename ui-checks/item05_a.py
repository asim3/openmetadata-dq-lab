from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers"); page.wait_for_timeout(4000)
    print("column header cells:", [" ".join(e.inner_text().split()) for e in page.locator("th").all()])
    print("email row:", " ".join(page.locator("tr[data-row-key='dqlab_mysql.default.dqlab.customers.email']").inner_text().split()))
    page.get_by_test_id("edit-description").first.click(); page.wait_for_timeout(1500)
    print([(e.get_attribute("data-testid"), " ".join(e.inner_text().split())) for e in page.locator("button:visible").all() if " ".join(e.inner_text().split()) in ("Save","Cancel","Update") or (e.get_attribute("data-testid") or "").endswith(("save","cancel"))])
    shot(page, "i05_desc_editor")
    b.close()
