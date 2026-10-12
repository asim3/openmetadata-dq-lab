"""Shared helpers for the UI checks: login, screenshots, .env values."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SHOTS = ROOT / "Screenshots"
SHOTS.mkdir(exist_ok=True)
BASE = "http://localhost:8585"


def env(name):
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"')
    raise KeyError(name)


def open_page(p, headless=True):
    browser = p.chromium.launch(channel="chrome", headless=headless)
    page = browser.new_context(viewport={"width": 1400, "height": 1000}).new_page()
    page.set_default_timeout(20000)
    page.goto(BASE)
    page.get_by_placeholder("Email").fill("admin@open-metadata.org")
    page.get_by_placeholder("Password").fill("admin")
    page.get_by_role("button", name="Sign In").click()
    page.wait_for_url(lambda u: "/signin" not in u)
    page.wait_for_load_state("networkidle")
    return browser, page


def shot(page, name):
    page.screenshot(path=str(SHOTS / f"{name}.png"))
