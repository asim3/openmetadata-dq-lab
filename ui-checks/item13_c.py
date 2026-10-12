from playwright.sync_api import sync_playwright
from dq import *
with sync_playwright() as p:
    b, page = open_page(p)
    T="dqlab_oracle.default.dqlab."
    for col, tt in (("hire_date","Column Values To Match Regex Pattern"),("status","Column Values To Be In Set"),("base_amount","Column Values To Be Between")):
        tbl = "SALARIES" if col=="base_amount" else "EMPLOYEES"
        page.goto(f"{BASE}/table/{T}{tbl}/profiler/data-quality"); page.wait_for_timeout(3500)
        page.get_by_role("button", name="Add").click(); page.wait_for_timeout(500)
        page.get_by_text("Test case", exact=True).click(); page.wait_for_timeout(1500)
        page.get_by_text("Column Level").first.click(); page.wait_for_timeout(800)
        page.get_by_text("Select Column", exact=True).last.click(); page.wait_for_timeout(700)
        page.get_by_role("option", name=col, exact=True).first.click(); page.wait_for_timeout(400)
        pick(page, "input[id='root/testType']", tt)
        print(tt, [(e.get_attribute("id"), e.get_attribute("placeholder")) for e in page.query_selector_all("input, textarea") if (e.get_attribute("id") or "").startswith(("root/","rc_select"))])
        shot(page, "dq_params_" + tt.split()[-1])
    b.close()
