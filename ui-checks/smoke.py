"""Smoke test: drive the host's Chrome, log in to OpenMetadata, take a screenshot."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "Screenshots"
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page()
    page.goto("http://localhost:8585")
    page.get_by_placeholder("Email").fill("admin@open-metadata.org")
    page.get_by_placeholder("Password").fill("admin")
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(lambda u: "/signin" not in u, timeout=30000)
    page.wait_for_load_state("networkidle")
    page.screenshot(path=str(OUT / "smoke.png"))
    print("title:", page.title(), "| url:", page.url)
    browser.close()
