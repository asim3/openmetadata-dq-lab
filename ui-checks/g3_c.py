from playwright.sync_api import sync_playwright
from common import *
def tag_row(page, table_fqn, column, tags):
    page.goto(f"{BASE}/table/{table_fqn}"); page.wait_for_timeout(4000)
    row = page.locator(f"tr[data-row-key='{table_fqn}.{column}']")
    row.get_by_text("Add", exact=True).first.click(); page.wait_for_timeout(1000)
    for t in tags:
        box = page.locator("#tagsForm_tags"); box.click(); box.fill(t); page.wait_for_timeout(2000)
        page.get_by_text(t, exact=True).last.click(); page.wait_for_timeout(500)
        box.fill(""); page.wait_for_timeout(300)
    page.get_by_role("button", name="Update").click(); page.wait_for_timeout(2500)
if __name__ == "__main__":
    with sync_playwright() as p:
        b, page = open_page(p)
        M="dqlab_mysql.default.dqlab."; O="dqlab_oracle.default.dqlab."
        tag_row(page, M+"customers", "email", ["Secret","Personal"]); print("email")
        tag_row(page, M+"customers", "full_name", ["Secret","Personal"]); print("full_name")
        tag_row(page, O+"EMPLOYEES", "full_name", ["Secret","Personal"]); print("emp full_name")
        tag_row(page, O+"SALARIES", "base_amount", ["Restricted"]); print("base_amount")
        b.close()
