"""Create a test case through the Add Test case drawer."""
from common import *


def pick(page, input_selector, text):
    """Type into the Test Type box and click the option with that exact title."""
    box = page.locator(input_selector).first
    box.click()
    box.fill(text)
    page.wait_for_timeout(700)
    page.get_by_text(text, exact=True).last.click()
    page.wait_for_timeout(500)


def create_test(page, table_fqn, name, test_type, column=None, params=None, sql=None, debug=False, description=None):
    page.goto(f"{BASE}/table/{table_fqn}/profiler/data-quality")
    page.wait_for_timeout(3500)
    page.get_by_role("button", name="Add").click(); page.wait_for_timeout(500)
    page.get_by_text("Test case", exact=True).click(); page.wait_for_timeout(1500)
    if column:
        page.get_by_text("Column Level").first.click(); page.wait_for_timeout(800)
        page.get_by_text("Select Column", exact=True).last.click(); page.wait_for_timeout(700)
        page.get_by_role("option", name=column, exact=True).first.click(); page.wait_for_timeout(400)
    pick(page, "input[id='root/testType']", test_type)
    params = params or {}
    if "regex" in params:
        page.get_by_placeholder("Enter a RegEx Pattern").fill(params["regex"])
    if "min" in params:
        page.get_by_placeholder("Enter a Min").fill(str(params["min"]))
    if "max" in params:
        page.get_by_placeholder("Enter a Max").fill(str(params["max"]))
    if "allowed" in params:
        vals = params["allowed"]
        for i, v in enumerate(vals):
            if i:
                page.get_by_test_id("add-allowedValues").click(); page.wait_for_timeout(300)
            page.get_by_placeholder("Enter a Allowed Values").nth(i).fill(v)
    if params.get("match_enum"):
        page.get_by_label("Match enum").check(force=True)
    if params.get("compute_row_count"):
        page.get_by_label("Compute Row Count").check(force=True)
    if sql:
        ed = page.locator(".test-case-form-body .cm-content, .test-case-form-body .CodeMirror, .test-case-form-body .ace_content").first
        ed.click(); page.keyboard.insert_text(sql); page.wait_for_timeout(300)
        sels = page.locator(".test-case-form-body select")
        print("strategy options:", sels.nth(0).locator("option").all_inner_texts(), "operator options:", sels.nth(1).locator("option").all_inner_texts())
        sels.nth(0).select_option(label=params.get("strategy", "ROWS"))
        sels.nth(1).select_option(label=params.get("operator", "<="))
        page.get_by_placeholder("Enter a Threshold").fill(str(params.get("threshold", 0)))
    page.locator("input[id='root/name']").fill(name)
    if description:
        ed = page.locator(".test-case-form-body .tiptap").first
        ed.click(); page.keyboard.insert_text(description)
    if debug:
        shot(page, "dq_debug")
        print([(e.get_attribute("id"), e.get_attribute("placeholder")) for e in page.query_selector_all("[role=dialog] input, .test-case-form-body input, .test-case-form-body textarea")])
    page.get_by_test_id("create-btn").click(); page.wait_for_timeout(3000)
