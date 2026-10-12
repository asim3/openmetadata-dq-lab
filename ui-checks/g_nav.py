from playwright.sync_api import sync_playwright
from common import *
with sync_playwright() as p:
    b, page = open_page(p)
    page.wait_for_timeout(1500)
    for label in ("Observability","Data Marketplace","Govern","Context Center"):
        page.get_by_text(label, exact=True).first.click(); page.wait_for_timeout(700)
    shot(page, "g_nav")
    links = page.evaluate("[...document.querySelectorAll('nav a, aside a, [class*=sidebar] a, [class*=menu] a')].filter(e=>e.offsetParent).map(e=>(e.innerText||'').trim()+' -> '+e.getAttribute('href'))")
    print("\n".join(dict.fromkeys(links)))
    b.close()
