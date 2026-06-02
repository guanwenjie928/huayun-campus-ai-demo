#!/usr/bin/env python3
"""
Intercept tenantListByPassword and fix moveLength to match blockX
"""
import json, time, os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = '/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/explore_screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ACCOUNT = '15612340001'
PASSWORD = 'Xx@123456'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-CN')
    page = context.new_page()

    captcha_data = [None]
    token_info = ['']
    request_payloads = []

    def on_response(response):
        if 'getCaptcha' in response.url:
            try:
                data = response.json()
                if data.get('data'):
                    captcha_data[0] = data['data']
                    cd = data['data']
                    print(f'[CAPTCHA] blockX={cd["blockX"]}')
            except: pass
        if 'auth/token' in response.url or 'get_token' in response.url:
            try:
                data = response.json()
                if data.get('data', {}).get('accessToken'):
                    token_info[0] = data['data']['accessToken']
                    print(f'[TOKEN] OK')
            except: pass
        if 'tenantListByPassword' in response.url:
            try:
                data = response.json()
                print(f'[TENANT RESP] {str(data)[:300]}')
            except: pass

    page.on('response', on_response)

    # Intercept REQUEST to tenantListByPassword to fix moveLength
    def intercept_request(route):
        if 'tenantListByPassword' in route.request.url:
            post_data = route.request.post_data
            print(f'[INTERCEPT] Original post data: {post_data}')

            # Parse and fix moveLength
            try:
                data = json.loads(post_data)
                if captcha_data[0]:
                    correct_move = captcha_data[0]['blockX']
                    original_move = data.get('moveLength', '?')
                    print(f'[INTERCEPT] moveLength: {original_move} -> {correct_move}')
                    data['moveLength'] = correct_move
                    fixed_data = json.dumps(data)
                    print(f'[INTERCEPT] Fixed: {fixed_data}')
                    route.continue_(post_data=fixed_data)
                else:
                    route.continue_()
            except Exception as e:
                print(f'[INTERCEPT] Error: {e}')
                route.continue_()
        else:
            route.continue_()

    page.route('**/tenantListByPassword**', intercept_request)

    # Navigate & login
    page.goto('https://pre-changpo.huayungpt.com/', wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(3000)
    page.locator('input[name="account"]').fill(ACCOUNT)
    page.locator('input[name="password"]').fill(PASSWORD)
    page.locator('input[name="agreement"]').check(force=True)
    page.wait_for_timeout(200)
    page.locator('button:has-text("登录")').click()
    page.wait_for_timeout(3000)

    if captcha_data[0]:
        cd = captcha_data[0]
        block_x = cd['blockX']
        slider_max = cd['canvasWidth'] - cd['blockWidth']
        ratio = block_x / slider_max

        # Find slider input
        slider_input = page.locator('.chakra-modal__body input[type="range"]').first
        try:
            box = slider_input.bounding_box()
            if box:
                target_x = box['x'] + ratio * box['width']
                target_y = box['y'] + box['height'] / 2
                print(f'Sliding to ({target_x:.0f}, {target_y:.0f}), ratio={ratio:.4f}')

                # Start from exact left edge
                page.mouse.move(box['x'], target_y)
                page.mouse.down()
                for i in range(1, 31):
                    cx = box['x'] + (target_x - box['x']) * i / 30
                    page.mouse.move(cx, target_y)
                    page.wait_for_timeout(10)
                page.wait_for_timeout(200)
                page.mouse.up()
        except Exception as e:
            print(f'Slider error: {e}')

    page.wait_for_timeout(8000)
    print(f'\nFinal URL: {page.url}')
    print(f'Login success: {"/login" not in page.url.lower()}')

    page.screenshot(path=os.path.join(SCREENSHOT_DIR, 'login_intercepted.png'), full_page=True)

    if token_info[0]:
        def inject_auth(route):
            headers = route.request.headers
            headers['Authorization'] = token_info[0]
            route.continue_(headers=headers)
        page.route('**/teacher-evaluate/**', inject_auth)
        page.route('**/student-evaluate/**', inject_auth)

    context.storage_state(path='/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/auth_state.json')
    browser.close()
