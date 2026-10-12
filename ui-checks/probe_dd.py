from playwright.sync_api import sync_playwright
from dq import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(f"{BASE}/table/dqlab_oracle.default.dqlab.EMPLOYEES/profiler/data-quality"); page.wait_for_timeout(3500)
    page.get_by_role("button", name="Add").click(); page.wait_for_timeout(500)
    page.get_by_text("Test case", exact=True).click(); page.wait_for_timeout(1500)
    pick(page, "input[id='root/testType']", "Custom SQL Query")
    shot(page, "dq_sql")
    print(page.evaluate("[...document.querySelectorAll('.test-case-form-body input, .test-case-form-body textarea, .test-case-form-body [role=switch], .test-case-form-body [contenteditable], .test-case-form-body .cm-content, .test-case-form-body select')].map(e=>e.tagName+'|'+e.id+'|'+(e.getAttribute('placeholder')||'')+'|'+(e.getAttribute('aria-label')||'')+'|'+e.className.toString().slice(0,30))"))
    b.close()
