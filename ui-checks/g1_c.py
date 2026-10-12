from playwright.sync_api import sync_playwright
from common import *
DOMAINS = [("Commerce","Commerce","Orders, customers and products sold online."),("HumanResources","Human Resources","Employees, pay and job history from the legacy HR system.")]
with sync_playwright() as p:
    b, page = open_page(p)
    for i,(name,disp,desc) in enumerate(DOMAINS):
        page.goto(BASE + "/domain"); page.wait_for_timeout(3000)
        page.get_by_test_id("add-domain").first.click(); page.wait_for_timeout(1200)
        page.locator("input[id='root/name']").fill(name)
        page.locator("input[id='root/displayName']").fill(disp)
        page.locator(".drawer-mode .tiptap, [role=dialog] .tiptap, .tiptap").first.click(); page.keyboard.insert_text(desc)
        page.get_by_text("Select Domain Type").click(); page.wait_for_timeout(500)
        page.get_by_text("Source-aligned", exact=True).last.click(); page.wait_for_timeout(400)
        page.locator("input[id='root/owners']").click(); page.keyboard.type("Data Governance"); page.wait_for_timeout(1500)
        shot(page, f"g1_6_domain_{i}")
        page.get_by_text("Data Governance Office", exact=True).last.click(); page.wait_for_timeout(500)
        shot(page, f"g1_6_domain_{i}b")
        page.mouse.click(1345, 966); page.wait_for_timeout(3500)
        print("saved", name, page.url)
    b.close()
