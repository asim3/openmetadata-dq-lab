from playwright.sync_api import sync_playwright
from common import *
TERMS = [("Customer","A person or company that has bought from us."),("Order","One purchase by a customer, with its status and amount."),("Employee","A person on the payroll of the organisation.")]
with sync_playwright() as p:
    b, page = open_page(p)
    for name, desc in TERMS:
        page.goto(BASE + "/glossary/BusinessGlossary"); page.wait_for_timeout(3000)
        page.get_by_role("button", name="Add term").click(); page.wait_for_timeout(1200)
        page.locator("input[id='root/name']").fill(name)
        page.locator(".tiptap[contenteditable=true]").last.click(); page.keyboard.insert_text(desc)
        page.get_by_role("button", name="Save").click(); page.wait_for_timeout(3500)
        print("saved", name)
    b.close()
