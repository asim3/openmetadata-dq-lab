from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings/members/teams"); page.wait_for_timeout(3500)
    page.get_by_role("button", name="Add").last.click(); page.wait_for_timeout(1200)
    page.locator("#add-team-nest-messages_name").fill("DataGovernanceOffice")
    page.locator("#add-team-nest-messages_displayName").fill("Data Governance Office")
    page.get_by_role("button", name="Save").click(); page.wait_for_timeout(3500)
    shot(page, "g1_3_team_page"); print(page.url)
    print([" ".join(t.inner_text().split()) for t in page.get_by_role("tab").all()])
    b.close()
