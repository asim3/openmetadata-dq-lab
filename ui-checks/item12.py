from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_oracle.default.dqlab.v_monthly_payroll/lineage"); page.wait_for_timeout(5000)
    page.mouse.click(620, 718)
    page.wait_for_timeout(1500)
    shot(page, "i12_edge")
    txt = page.locator("body").inner_text()
    i = txt.find("WHERE")
    print("has WHERE:", i>=0, "|", txt[max(0,i-300):i+80].replace("\n"," ") if i>=0 else "")
    b.close()
