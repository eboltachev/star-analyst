import subprocess
import time
from urllib import request

import pytest

playwright = pytest.importorskip("playwright.sync_api")
pytest.importorskip("fastapi")


@pytest.mark.e2e
def test_full_flow_playwright():
    proc = subprocess.Popen([
        "python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8011"
    ])
    time.sleep(2)
    try:
        req = request.Request("http://127.0.0.1:8011/seed-admin", method="POST")
        request.urlopen(req, timeout=5).read()
        with playwright.sync_api.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://127.0.0.1:8011/login")
            page.fill('input[name="email"]', "admin@example.com")
            page.fill('input[name="password"]', "admin123")
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            assert "Новая проверка" in page.content()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
