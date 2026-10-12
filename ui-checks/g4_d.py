from playwright.sync_api import sync_playwright
from common import *
TAGS = [("Reference","Reference","Slow-changing lookup data, such as departments."),("Master","Master","Core business entities, such as customers."),("Transactional","Transactional","Records of events, such as orders and pay.")]
TABLES = [("dqlab_mysql.default.dqlab.customers","Master"),("dqlab_mysql.default.dqlab.products","Master"),("dqlab_oracle.default.dqlab.EMPLOYEES","Master"),("dqlab_mysql.default.dqlab.orders","Transactional"),("dqlab_oracle.default.dqlab.SALARIES","Transactional")]
with sync_playwright() as p:
    b, page = open_page(p)
    for fq, tag in TABLES:
        page.goto(f"{BASE}/table/{fq}"); page.wait_for_timeout(4000)
        lab = page.get_by_text("Tags", exact=True).last
        btn = lab.locator("xpath=following::*[@data-testid='add-tag' or @data-testid='edit-button'][1]")
        btn.click(); page.wait_for_timeout(1000)
        box = page.locator("#tagsForm_tags"); box.click(); box.fill(tag); page.wait_for_timeout(2000)
        page.get_by_text(tag, exact=True).last.click(); page.wait_for_timeout(500)
        page.get_by_role("button", name="Update").click(); page.wait_for_timeout(2500); print("kind", fq.split(".")[-1], tag)
    b.close()
