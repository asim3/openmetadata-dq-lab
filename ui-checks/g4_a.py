from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.orders"); page.wait_for_timeout(4000)
    for tid in ("edit-tier","edit-certification","edit-retention-period-button"):
        page.get_by_test_id(tid).click(); page.wait_for_timeout(1000)
        shot(page, "g4_"+tid)
        print(tid, [" ".join(e.inner_text().split()) for e in page.locator("[role=radio], [role=option], [class*=card], label, input").all() if e.is_visible()][:14])
        page.keyboard.press("Escape"); page.wait_for_timeout(500)
    b.close()
