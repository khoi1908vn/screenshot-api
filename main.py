
from pyppeteer import launch
import asyncio,os, requests, subprocess
from aiohttp import web, ClientSession


async def get_screenshot(url, resolution: int = 720, delay: int = 0):
    global chromium_path
    window_height = int(resolution*16/9)
    window_width = resolution
    browser = await launch(executablePath = chromium_path, headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-position=0,0', '--enable-features=WebContentsForceDark'], handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False)
    page = await browser.newPage()
    await page.setViewport({'width': window_width, 'height': window_height})
    await page._client.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': '/dev/null'})
    await page.goto(url)
    await page.waitForNavigation()
    await asyncio.sleep(3 + delay)
    elements = await page.Jx(f"//*[contains(text(), '{ip}')]")
    for element in elements:
        await page.evaluate("(element) => element.innerText = '<the host ip address>'", element)
    image_bytes = await page.screenshot()
    await browser.close()
    return image_bytes

routes = web.RouteTableDef()

@routes.get('/image')
async def image(request):
    try:
        auth_header = request.query.get('authorization')
        if not auth_header or not (lambda key: key in list(os.environ.get("allowed-keys", ['testkey_'])))(auth_header):
            return web.Response(text='Invalid token', status=401)
        url = request.query.get('url')
        resolution = int(request.query.get('resolution', 720))
        delay = int(request.query.get('delay', 7))
        image_binary = await get_screenshot(url, resolution, delay)
        return web.Response(body=image_binary, content_type='image/png')
    except Exception as e:
        return web.Response(text=f'Error: {e}', status=500)

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
    global chromium_path
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    web.run_app(app, host='0.0.0.0', port=8000)
    chromium_path = subprocess.check_output(['which', 'chromium']).strip().decode('utf-8')
