from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
import asyncio

async def get_screenshot(url, resolution: int, delay: int = 7):
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
    with webdriver.Chrome(options=options) as driver:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body[not(@class='loading')]")))
        await asyncio.sleep(3 + delay)
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{ip}')]")
        for element in elements: driver.execute_script("arguments[0].innerText = arguments[1];", element, '<the host ip address>')
        image_bytes = driver.get_screenshot_as_png()
    return image_bytes

from flask import Flask, request, Response
import requests, os

app = Flask(__name__)

is_key_usable = lambda key: key in list(os.environ.get("allowed-keys", []))
@app.route('/image')
async def image():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[0].lower() != 'bearer' or not is_key_usable(auth_header.split()[1]):
        return Response('Invalid token', 401)
    url = request.args.get('url')
    resolution = int(request.args.get('resolution'))
    delay = int(request.args.get('delay', 7))
    try:
        image_binary = await get_screenshot(url, resolution, delay)
        response = Response(image_binary)
        response.headers.set('Content-Type', 'image/png')
        return response
    except Exception as e:
        return Response(f'Error: {e}', 500)


if __name__ == '__main__':
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    app.run()

