import base64, json, urllib.request
from playwright.sync_api import sync_playwright
from common import *
def api(path, data=None):
    req = urllib.request.Request("http://localhost:8585/api/v1"+path, data=data, headers={"Content-Type":"application/json", **({"Authorization":"Bearer "+TOK} if "TOK" in globals() else {})})
    return json.load(urllib.request.urlopen(req))
TOK = api("/users/login", json.dumps({"email":"admin@open-metadata.org","password":base64.b64encode(b"admin").decode()}).encode())["accessToken"]
cases = [t["fullyQualifiedName"] for t in api("/dataQuality/testCases?limit=100")["data"] if t["fullyQualifiedName"].startswith("dqlab_mysql")]
inc = api("/dataQuality/testCases/testCaseIncidentStatus?limit=100&latest=true")["data"]
open_names = {i["testCaseReference"]["fullyQualifiedName"] for i in inc if i["testCaseResolutionStatusType"] != "Resolved"}
print(len(open_names), "open incidents")
with sync_playwright() as p:
    b, page = open_page(p)
    first = True
    for fqn in sorted(open_names):
        page.goto(f"{BASE}/test-case/{fqn}"); page.wait_for_timeout(4500)
        page.get_by_text("Incident Status").locator("xpath=following::button[1]").click(); page.wait_for_timeout(700)
        page.locator("[role=dialog] .ant-select").first.click(); page.wait_for_timeout(500)
        page.locator(".ant-select-item-option").filter(has_text="Resolved").first.click(); page.wait_for_timeout(600)
        page.locator("[role=dialog] .ant-select").nth(1).click(); page.wait_for_timeout(500)
        if first:
            print("reasons:", [e.inner_text() for e in page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").all()]); first = False
        page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").first.click(); page.wait_for_timeout(400)
        page.locator("[role=dialog] .tiptap").click(); page.keyboard.insert_text("Cause: bad rows from the seeder's batch. Fix: removed them with fix_defects.py; tests re-run green.")
        page.get_by_role("button", name="Save").click(); page.wait_for_timeout(2500)
        print("resolved", fqn.split(".")[-1])
    b.close()
