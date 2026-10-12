from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/glossary/BusinessGlossary"); page.wait_for_timeout(3500)
    page.get_by_text("Reviewers", exact=True).locator("xpath=following::button[1]").click(); page.wait_for_timeout(1000)
    page.get_by_role("tab", name="Users").click(); page.wait_for_timeout(800)
    page.get_by_text("admin", exact=True).last.click(); page.wait_for_timeout(300)
    page.get_by_text("Data Steward", exact=True).last.click(); page.wait_for_timeout(300)
    shot(page, "g2_6_reviewer_swap")
    page.get_by_role("button", name="Update").click(); page.wait_for_timeout(2500)
    page.get_by_role("button", name="Add term").click(); page.wait_for_timeout(1200)
    page.locator("input[id='root/name']").fill("Product")
    page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text("Something we sell, with a SKU and a price.")
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(3500)
    shot(page, "g2_7_product_term"); print(page.url)
    b.close()
