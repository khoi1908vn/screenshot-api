import asyncio
"Playwright API"
from playwright.async_api import async_playwright
async def get_screenshot_playwright(url: str, resolution: int, delay: int = 7):
    global ip
    window_height = int(resolution*16/9)
    window_width = resolution
    async with async_playwright() as p:
        browser = await p.chromium.launch(downloads_path='/dev/null', headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--headless', '--disable-gpu', '--window-position=0,0', '--enable-features=WebContentsForceDark'])
        context = await browser.new_context(accept_downloads=False)
        page = await context.new_page()
        await page.set_viewport_size({"width": window_width, "height": window_height})
        await page.goto(url)
        await page.wait_for_selector("body:not(.loading)")
        await asyncio.sleep(3 + delay)
        elements = await page.query_selector_all(f"//*[contains(text(), '{ip}')]")
        for element in elements: await element.evaluate(f"el => el.textContent = '{ip}'")
        image_bytes = await page.screenshot()
        browser.close()
    return image_bytes

"Selenium.py"
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
async def get_screenshot_selenium(url, resolution: int, delay: int = 7):
    global ip
    window_height = int(resolution*16/9)
    window_width = resolution
    options = Options()
    for arg in ['--no-sandbox', '--disable-dev-shm-usage', '--headless', '--disable-gpu', '--window-position=0,0', f'--window-size={window_height},{window_width}', '--enable-features=WebContentsForceDark']: options.add_argument(arg)
    prefs = {
    "download_restrictions": 3,
    "download.open_pdf_in_system_reader": False,
    "download.prompt_for_download": True,
    "download.default_directory": "/dev/null",
    "plugins.always_open_pdf_externally": False
    }
    options.add_experimental_option("prefs", prefs)
    async with webdriver.Chrome(options=options) as driver:
        await driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body[not(@class='loading')]")))
        await asyncio.sleep(3 + delay)
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{ip}')]")
        for element in elements: driver.execute_script("arguments[0].innerText = arguments[1];", element, '<the host ip address>')
        image_bytes = await driver.get_screenshot_as_png()
    return await image_bytes