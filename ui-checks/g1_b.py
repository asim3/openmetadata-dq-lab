from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.goto(BASE + "/settings/members/teams/DataGovernanceOffice"); page.wait_for_timeout(3500)
    print([" ".join(t.inner_text().split()) for t in page.get_by_role("tab").all()])
    page.get_by_role("tab", name="Assets").click(); page.wait_for_timeout(2500)
    shot(page, "g1_13_team_assets")
    t=" ".join(page.locator("body").inner_text().split()); print(t[t.find("Assets"):][:300])
    b.close()
