import os
from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p, user="data.steward@example.com", password=os.environ["STEWARD_PW"])
    page.goto(f"{BASE}/table/dqlab_mysql.default.dqlab.orders/activity_feed/tasks"); page.wait_for_timeout(5000)
    shot(page, "g5_7_steward_task")
    page.get_by_test_id("workflow-task-action-primary").click() if page.get_by_test_id("workflow-task-action-primary").count() else page.get_by_text("Approve", exact=True).first.click()
    page.wait_for_timeout(1200)
    if page.get_by_role("button", name="Ok").count(): page.get_by_role("button", name="Ok").click()
    page.wait_for_timeout(3500)
    b.close()
