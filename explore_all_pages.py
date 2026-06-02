#!/usr/bin/env python3
"""
通过实际点击侧边栏菜单获取真实URL映射
在每个系统主页，逐个点击侧边栏，记录URL变化
"""
import json, time, os
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = '/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/explore_screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

ACCOUNT = '15612340001'
PASSWORD = 'Xx@123456'
BASE = 'https://pre-changpo.huayungpt.com'

def do_login(page):
    captcha_data = [None]
    token_info = ['']

    def on_response(response):
        if 'getCaptcha' in response.url:
            try:
                data = response.json()
                if data.get('data'):
                    captcha_data[0] = data['data']
            except: pass
        if 'get_token' in response.url:
            try:
                data = response.json()
                if data.get('data', {}).get('accessToken'):
                    token_info[0] = data['data']['accessToken']
            except: pass

    page.on('response', on_response)

    def intercept_tenant(route):
        if 'tenantListByPassword' in route.request.url and captcha_data[0]:
            try:
                data = json.loads(route.request.post_data)
                data['moveLength'] = captcha_data[0]['blockX']
                route.continue_(post_data=json.dumps(data))
                return
            except: pass
        route.continue_()
    page.route('**/tenantListByPassword**', intercept_tenant)

    page.goto(BASE, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(3000)

    if '/login' not in page.url.lower():
        try:
            token = page.evaluate("localStorage.getItem('token')")
            if token:
                token_info[0] = token.replace('Bearer ', '')
        except: pass
        return token_info[0] or True

    page.locator('input[name="account"]').fill(ACCOUNT)
    page.locator('input[name="password"]').fill(PASSWORD)
    page.locator('input[name="agreement"]').check(force=True)
    page.wait_for_timeout(300)
    page.locator('button:has-text("登录")').click()
    page.wait_for_timeout(3000)

    if captcha_data[0]:
        cd = captcha_data[0]
        ratio = cd['blockX'] / (cd['canvasWidth'] - cd['blockWidth'])
        try:
            slider_input = page.locator('.chakra-modal__body input[type="range"]').first
            box = slider_input.bounding_box()
            if box:
                target_x = box['x'] + ratio * box['width']
                target_y = box['y'] + box['height'] / 2
                page.mouse.move(box['x'], target_y)
                page.mouse.down()
                for i in range(1, 25):
                    page.mouse.move(box['x'] + (target_x - box['x']) * i / 25, target_y)
                    page.wait_for_timeout(12)
                page.wait_for_timeout(300)
                page.mouse.up()
        except: pass

    page.wait_for_timeout(8000)
    return token_info[0] or ('/login' not in page.url.lower())

def click_sidebar_items_and_record(page, base_url, system_name):
    """Navigate to base page, then click sidebar items one by one, recording URLs"""
    print(f'\n{"="*60}')
    print(f'CLICKING THROUGH: {system_name}')
    print(f'Base URL: {base_url}')
    print(f'{"="*60}')

    page.goto(base_url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(3000)

    # First, let's understand the sidebar DOM structure
    # Dump all clickable elements in the sidebar area
    sidebar_info = page.evaluate('''() => {
        const items = [];
        const allElements = document.querySelectorAll('*');
        allElements.forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.x < 280 && rect.x > 5 && rect.y > 50 && rect.width > 30 && rect.height > 10 && rect.height < 80) {
                const text = el.textContent.trim();
                if (text && text.length >= 2 && text.length < 30) {
                    items.push({
                        tag: el.tagName,
                        text: text,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        w: Math.round(rect.width),
                        h: Math.round(rect.height),
                        cls: (el.className && typeof el.className === 'string') ? el.className.substring(0, 80) : '',
                        role: el.getAttribute('role') || '',
                        clickable: el.onclick !== null || el.getAttribute('role') === 'button' || el.tagName === 'A' || el.tagName === 'BUTTON'
                    });
                }
            }
        });
        return items;
    }''')

    print(f'\nSidebar elements found: {len(sidebar_info)}')
    # Group by similar y positions
    seen_texts = set()
    unique_items = []
    for item in sidebar_info:
        if item['text'] not in seen_texts:
            seen_texts.add(item['text'])
            unique_items.append(item)
    unique_items.sort(key=lambda x: x['y'])

    print('Unique sidebar items (by position):')
    for item in unique_items:
        print(f'  y={item["y"]:4d} x={item["x"]:3d} {item["tag"]:5s} [{item.get("role",""):8s}] "{item["text"]}" cls={item["cls"][:60]}')

    # Now click each unique sidebar item and record URL change
    results = []
    for item in unique_items:
        text = item['text']
        # Skip header/title text and page content bleeding into sidebar
        if len(text) > 25 or '学年' in text or '长坡' in text:
            continue

        print(f'\nClicking: "{text}" (y={item["y"]})')

        # Navigate back to base first to reset
        page.goto(base_url, wait_until='networkidle', timeout=15000)
        page.wait_for_timeout(1500)

        # Try to click using the text content
        clicked = False
        # Try to click by finding the element at the correct position
        selector = f'text="{text}"'
        try:
            candidates = page.locator(selector).all()
            for c in candidates:
                try:
                    box = c.bounding_box()
                    if box and box['x'] < 280:
                        c.click()
                        page.wait_for_timeout(2000)
                        new_url = page.url
                        print(f'  -> URL: {new_url[:120]}')
                        results.append({
                            'text': text,
                            'url': new_url,
                            'y': item['y'],
                            'changed': new_url != base_url
                        })
                        clicked = True
                        break
                except: pass
        except: pass

        if not clicked:
            print(f'  -> FAILED to click')

    return results


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='zh-CN')
        page = context.new_page()

        # Login
        print('=== LOGIN ===')
        result = do_login(page)
        if not result:
            print('Login failed')
            browser.close()
            return

        token = result if isinstance(result, str) else ''
        if token:
            def inject_auth(route):
                headers = route.request.headers
                headers['Authorization'] = token
                route.continue_(headers=headers)
            page.route('**/teacher-evaluate/**', inject_auth)
            page.route('**/student-evaluate/**', inject_auth)

        context.storage_state(path='/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/auth_state.json')

        # Explore teacher system
        teacher_base = f'{BASE}/teacher-evaluate/evaluateTaskManage/taskManage'
        teacher_results = click_sidebar_items_and_record(page, teacher_base, 'TEACHER')

        # Explore student system
        student_base = f'{BASE}/student-evaluate/evaluateTaskManage/taskManage?rBK=1'
        student_results = click_sidebar_items_and_record(page, student_base, 'STUDENT')

        browser.close()

        # Save results
        url_map = {
            'teacher': teacher_results,
            'student': student_results
        }
        with open(os.path.join(SCREENSHOT_DIR, 'url_map.json'), 'w', encoding='utf-8') as f:
            json.dump(url_map, f, ensure_ascii=False, indent=2)

        print(f'\n{"="*60}')
        print('URL MAP:')
        for system, items in url_map.items():
            print(f'\n{system.upper()}:')
            for item in items:
                print(f'  {item["text"]}: {item["url"]}')

if __name__ == '__main__':
    main()
