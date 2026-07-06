"""Video icin ekran goruntuleri — playwright ile prod sitesinden (EN, 1920x1080)."""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

BASE = "https://atradebot.xyz"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shots")
SESSION = sys.argv[1] if len(sys.argv) > 1 else ""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080},
                                        device_scale_factor=1)
        # dil: EN
        await ctx.add_init_script("localStorage.setItem('lang','en')")
        page = await ctx.new_page()

        # ---- landing sahneleri ----
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1800)   # fade-up animasyonlari otursun
        await page.screenshot(path=f"{OUT}/01_hero.png")

        await page.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
        for name, sel in [("02_features", ".feature"), ("03_tiers", ".tier"),
                          ("04_how", ".step")]:
            await page.locator(sel).first.scroll_into_view_if_needed()
            await page.wait_for_timeout(700)
            await page.screenshot(path=f"{OUT}/{name}.png")

        # ---- panel sahneleri (demo oturum cerezi) ----
        if SESSION:
            await ctx.add_cookies([{"name": "session", "value": SESSION,
                                    "domain": "atradebot.xyz", "path": "/"}])
            await page.goto(BASE, wait_until="networkidle")
            await page.wait_for_timeout(2500)
            await page.screenshot(path=f"{OUT}/05_dashboard.png")

            # risk karti
            await page.evaluate("document.querySelectorAll('.reveal').forEach(e=>e.classList.add('in'))")
            risk = page.locator(".presets").first
            await risk.scroll_into_view_if_needed()
            await page.wait_for_timeout(1200)   # sympick yuklenmesi
            await page.screenshot(path=f"{OUT}/06_risk.png")

            # market secici odakli
            sp = page.locator("#sympick")
            await sp.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUT}/07_symbols.png")

            # bot + telegram kartlari
            bot = page.locator("#botstate")
            await bot.scroll_into_view_if_needed()
            await page.wait_for_timeout(11000)  # loadState olaylari cekssin
            await page.screenshot(path=f"{OUT}/08_bot.png")

        await browser.close()
        print("bitti:", sorted(os.listdir(OUT)))

asyncio.run(main())
