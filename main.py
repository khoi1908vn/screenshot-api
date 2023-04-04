import os, requests, time
from flask import Flask, request, Response
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
ratelimit = 0
app = Flask(__name__)

def get_screenshot(url, resolution: int, delay: int = 7) -> bytes:
    ratelimit += 1
    global ip
    window_height = int(resolution*16/9)
    window_width = resolution
    options = Options()
    for arg in ['--no-sandbox', '--disable-dev-shm-usage', '--headless', '--disable-gpu', '--window-position=0,0', f'--window-size={window_height},{window_width}', '--enable-features=WebContentsForceDark']:
        options.add_argument(arg)
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
        time.sleep(3 + delay)
        if ip:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{ip}')]")
            for element in elements:
                driver.execute_script("arguments[0].innerText = arguments[1];", element, '<the host ip address>')
        screenshot_bytes = driver.get_screenshot_as_png()
    ratelimit += -1
    return screenshot_bytes

@app.route('/image')
def image():
    try:
        auth_header = request.headers.get('authorization')
        if not auth_header:
            return Response('Missing authorization', status=400)
        if auth_header != os.environ.get('allowed_key', 'testkey_'):
            return Response(f'Invalid token, given {auth_header}', status=401)
        if ratelimit > 2:
            return Response("Gloal-Ratelimited", status=429)
        url = request.args.get('url')
        resolution = int(request.args.get('resolution', 720))
        delay = int(request.args.get('delay', 7))
        image_binary = get_screenshot(url, resolution, delay)
        return Response(image_binary, content_type='image/png')
    except Exception as e:
        print(e)
        return Response(f'Error: {e}', status=500)

if __name__ == '__main__':
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    app.run(host='0.0.0.0', port=8000)
    ratelimit = 0
