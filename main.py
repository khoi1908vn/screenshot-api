import os
import time
import requests
from fastapi import FastAPI, Response, Header
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

app = FastAPI()

class BrowserPool:
    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        self.pool = []
        self.lock = Lock()
        self.create_pool()
        
    def create_pool(self):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--enable-features=WebContentsForceDark')
        
        prefs = {
            "download_restrictions": 3,
            "download.open_pdf_in_system_reader": False,
            "download.prompt_for_download": True,
            "download.default_directory": "/dev/null",
            "plugins.always_open_pdf_externally": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        for _ in range(self.pool_size):
            browser = webdriver.Chrome(options=chrome_options)
            self.pool.append(browser)
    
    def get_browser(self):
        with self.lock:
            browser = self.pool.pop()
        return browser
    
    def release_browser(self, browser):
        with self.lock:
            self.pool.append(browser)
            
browser_pool = BrowserPool()

def get_screenshot(browser, url, resolution: int, delay: int = 7) -> bytes:
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    window_height = int(resolution*16/9)
    window_width = resolution
    els = time.time()
    browser.get(url)
    wait = WebDriverWait(browser, 10)
    wait.until(EC.presence_of_element_located((By.XPATH, "//body[not(@class='loading')]")))
    time.sleep(3 + delay)
    if ip:
        elements = browser.find_elements(By.XPATH, f"//*[contains(text(), '{ip}')]")
        for element in elements:
            browser.execute_script("arguments[0].innerText = arguments[1];", element, '<the host ip address>')
    screenshot_bytes = browser.get_screenshot_as_png()
    elapsed = 1000*(time.time() - els) # in ms
    return screenshot_bytes, round(elapsed)

@app.get('/')
def root():
    return 'Hello there'

@app.get('/image')
def image(resolution: int = 720, delay: int = 7, authorization: str = Header(None), url: str = Header(None)):
    try:
        if not authorization:
            return Response('Missing authorization', status_code=400)
        if authorization != os.environ.get('allowed_key', 'testkey_'):
            return Response(f'Invalid token, given {authorization}', status_code=401)
        if not url:
            return Response('Missing URL in header', status_code=400)
        browser = browser_pool.get_browser()
        image_binary, elapsed = get_screenshot(browser, url, resolution, delay)
        browser.execute_script("window.close()")
        browser_pool.release_browser(browser)
        with open('log.txt', 'a+') as f:
            f.write(str(int(time.time())) + ' ' + f'{url} | {resolution}p | {elapsed}ms')
        return Response(image_binary, media_type='image/png', headers={"X-Elapsed-Time": str(elapsed)})
    except Exception as e:
        print(e)
        return Response(f'Error: {e}', status_code=500)

