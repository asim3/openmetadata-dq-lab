from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.customers/contract"); page.wait_for_timeout(4000)
    page.get_by_test_id("add-contract-button").click(); page.wait_for_timeout(1000)
    shot(page, "g5_13_contract")
    print([" ".join(e.inner_text().split()) for e in page.locator("[role=menuitem], [role=option], li").all() if e.is_visible()][:8])
    page.get_by_text("Create Contract", exact=False).first.click(); page.wait_for_timeout(2500)
    page.get_by_placeholder("Please enter Contract name").fill("customers_contract"); page.wait_for_timeout(300)
    page.get_by_text("Please Select a Owners", exact=True).click(); page.wait_for_timeout(1000)
    shot(page, "g5_14_contract_owner")
    page.get_by_text("Data Governance Office", exact=True).last.click(); page.wait_for_timeout(800)
    page.get_by_text("Contract Details", exact=True).first.click()
    page.get_by_text("Schema", exact=True).first.click(); page.wait_for_timeout(1500); shot(page, "g5_14_contract_schema")
    page.get_by_text("Quality", exact=True).first.click(); page.wait_for_timeout(1500); shot(page, "g5_14_contract_quality")
    print(" ".join(page.locator("body").inner_text().split())[900:1500])
    b.close()
