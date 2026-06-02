#!/usr/bin/env python3
"""
验证系统操作演示.html的动画效果
截取初始、中期、完成三个截图
"""
import time
from playwright.sync_api import sync_playwright

html_path = '/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/系统操作演示.html'
screenshots_dir = '/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1200})

    # Load the HTML file
    page.goto(f'file://{html_path}')
    page.wait_for_load_state('networkidle')

    # Screenshot 1: Initial state (before playing)
    time.sleep(1)
    page.screenshot(path=f'{screenshots_dir}/demo_screenshot_1_initial.png', full_page=True)
    print("✓ Screenshot 1: Initial state saved")

    # Click the play button to start the animation
    play_btn = page.locator('#play-btn')
    play_btn.click()
    print("✓ Clicked play button")

    # Screenshot 2: Mid-animation (wait for ~10 seconds)
    time.sleep(12)
    page.screenshot(path=f'{screenshots_dir}/demo_screenshot_2_mid.png', full_page=True)
    print("✓ Screenshot 2: Mid-animation saved")

    # Screenshot 3: Complete state (wait for ~25 more seconds for full animation)
    time.sleep(25)
    page.screenshot(path=f'{screenshots_dir}/demo_screenshot_3_complete.png', full_page=True)
    print("✓ Screenshot 3: Complete state saved")

    browser.close()

print("\n✅ All screenshots saved to:")
print(f"  1. {screenshots_dir}/demo_screenshot_1_initial.png")
print(f"  2. {screenshots_dir}/demo_screenshot_2_mid.png")
print(f"  3. {screenshots_dir}/demo_screenshot_3_complete.png")
