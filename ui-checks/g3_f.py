from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    for fq in ("dqlab_mysql.default.dqlab.customers","dqlab_mysql.default.dqlab.products","dqlab_oracle.default.dqlab.EMPLOYEES","dqlab_oracle.default.dqlab.SALARIES"):
        page.goto(f"{BASE}/table/{fq}/custom_properties"); page.wait_for_timeout(4000)
        page.get_by_text("Not set").first.locator("xpath=following::*[name()='svg' or self::button][1]").click(); page.wait_for_timeout(800)
        inp = page.locator("input[type=text]:visible, textarea:visible").last
        inp.fill("2026-10-12"); page.wait_for_timeout(300)
        shot(page, "g3_9_cp_edit")
        page.locator("[data-testid='inline-save-btn'], button[data-testid*=save]").first.click(); page.wait_for_timeout(2000)
        print("set", fq.split(".")[-1])
    b.close()
