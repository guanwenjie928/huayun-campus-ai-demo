#!/usr/bin/env python3
"""Verify the demo HTML works correctly"""
import time
from playwright.sync_api import sync_playwright

html_path = '/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/系统操作演示.html'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 1000})

    # Collect console errors
    errors = []
    page.on('console', lambda msg: errors.append(f'[{msg.type}] {msg.text}') if msg.type in ['error','warning'] else None)
    page.on('pageerror', lambda err: errors.append(f'[PAGE ERROR] {err}'))

    page.goto(f'file://{html_path}')
    page.wait_for_load_state('networkidle')
    time.sleep(2)

    # Check for JS errors
    if errors:
        print('JS ERRORS/WARNINGS:')
        for e in errors:
            print(f'  {e}')
    else:
        print('No JS errors')

    # Take initial screenshot
    page.screenshot(path='/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/demo_v2_initial.png', full_page=True)
    print('Initial screenshot saved')

    # Click play and capture mid-way
    page.locator('#play-btn').click()
    print('Play clicked')
    time.sleep(20)
    page.screenshot(path='/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/demo_v2_mid.png', full_page=True)
    print('Mid screenshot saved')

    time.sleep(40)
    page.screenshot(path='/data/1c4f8774-260b-4396-a6ed-6913c7eee5b2/demo_v2_end.png', full_page=True)
    print('End screenshot saved')

    browser.close()
    print('Done')
