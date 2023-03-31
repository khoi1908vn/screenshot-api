import asyncio,os, requests
from aiohttp import web, ClientSession


from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
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
    async with webdriver.Chrome(options=options) as driver:
        await driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, "//body[not(@class='loading')]")))
        await asyncio.sleep(3 + delay)
        elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{ip}')]")
        for element in elements: driver.execute_script("arguments[0].innerText = arguments[1];", element, '<the host ip address>')
        image_bytes = await driver.get_screenshot_as_png()
    return await image_bytes

routes = web.RouteTableDef()

@routes.get('/image')
async def image(request):
    #try:
        auth_header = request.headers.get('authorization')
        # if (not auth_header) or (not (lambda key: key in list(os.environ.get("allowed-keys", ['testkey_'])))(auth_header)):
        if not auth_header:
            return web.Response(text='Missing authorization', status = 400)
        if auth_header not in list(os.environ.get("allowed-keys", ['testkey_']))
            return web.Response(text='Invalid token', status=401)
        url = request.query.get('url')
        resolution = int(request.query.get('resolution', 720))
        delay = int(request.query.get('delay', 7))
        image_binary = await get_screenshot(url, resolution, delay)
        return web.Response(body=image_binary, content_type='image/png')
    #except Exception as e:
     #   return web.Response(text=f'Error: {e}', status=500)

# Example on a request
async def examplerequest(api_url, token, url, resolution, delay=7):
    params = {'url': url, 'resolution': resolution, 'delay': delay, 'authorization': token}
    async with ClientSession() as session:
        async with session.get(api_url, params=params) as response:
            response.raise_for_status()
            image_data = await response.read()
    return image_data

app = web.Application()
app.add_routes(routes)

if __name__ == '__main__':
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    web.run_app(app, host='0.0.0.0', port=8000)
