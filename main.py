
from pyppeteer import launch
import asyncio


async def get_screenshot(url, resolution: int, delay: int = 7):
    window_height = int(resolution*16/9)
    window_width = resolution
    async with launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-position=0,0', '--enable-features=WebContentsForceDark']) as browser:
        async with browser.newPage() as page:
            await page.setViewport({'width': window_width, 'height': window_height})
            await page._client.send('Page.setDownloadBehavior', {'behavior': 'allow', 'downloadPath': '/dev/null'})
            await page.goto(url)
            await page.waitForNavigation()
            await asyncio.sleep(3 + delay)
            elements = await page.Jx(f"//*[contains(text(), '{ip}')]")
            for element in elements:
                await page.evaluate("(element) => element.innerText = '<the host ip address>'", element)
            image_bytes = await page.screenshot()
    return image_bytes

from flask import Flask, request, Response
app = Flask(__name__)
@app.route('/image')
async def image():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header.split()[0].lower() != 'bearer' or not (lambda key: key in list(os.environ.get("allowed-keys", [])))(auth_header.split()[1]):
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

import requests, os
if __name__ == '__main__':
    ip = requests.get('https://ipv4.icanhazip.com').text.strip()
    app.run()

