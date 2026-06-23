#!/usr/bin/env python3
"""アプリ画面のスクリーンショットを取得する"""

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DEBUG", "true")

import django

django.setup()

from django.test import Client

OUTPUT_DIR = Path(__file__).parent / "screenshots"
BASE_URL = "http://127.0.0.1:8000"
PREVIEW_PORT = 8765
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SCREENS = [
    ("01_login", "/login/", False),
    ("02_role_select", "/", True),
    ("03_ice_register", "/register/", True),
    ("04_food_register", "/food/register/", True),
    ("05_shavedice_register", "/shavedice/register/", True),
    ("06_food_kitchen", "/food/kitchen/", True),
    ("07_ice_deshap", "/deshap/", True),
    ("08_shavedice_waittime", "/shavedice/waittime/", True),
]


def make_client(logged_in: bool) -> Client:
    client = Client(HTTP_HOST="localhost")
    if logged_in:
        session = client.session
        session["logged_in"] = True
        session.save()
    return client


def save_html_snapshots() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, path, needs_login in SCREENS:
        client = make_client(needs_login)
        response = client.get(path, follow=True)
        if response.status_code != 200:
            raise RuntimeError(f"{name} ({path}): HTTP {response.status_code}")

        html = response.content.decode("utf-8")
        html = html.replace('href="/static/', f'href="{BASE_URL}/static/')
        html = html.replace('src="/static/', f'src="{BASE_URL}/static/')
        html = html.replace('action="/', f'action="{BASE_URL}/')
        (OUTPUT_DIR / f"{name}.html").write_text(html, encoding="utf-8")


def capture_png(name: str) -> Path:
    if not Path(CHROME).exists():
        raise FileNotFoundError("Google Chrome が見つかりません")

    png_path = OUTPUT_DIR / f"{name}.png"
    url = f"http://127.0.0.1:{PREVIEW_PORT}/{name}.html"

    if name == "01_login":
        url = f"{BASE_URL}/login/"

    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1280,900",
        "--virtual-time-budget=5000",
        "--run-all-compositor-stages-before-draw",
        f"--screenshot={png_path.resolve()}",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    if result.returncode != 0 or not png_path.exists():
        raise RuntimeError(f"{name} の取得に失敗: {result.stderr}")
    return png_path


def main() -> int:
    print("📸 スクリーンショット取得を開始します...")
    save_html_snapshots()

    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PREVIEW_PORT)],
        cwd=OUTPUT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)

    try:
        for name, _, _ in SCREENS:
            png = capture_png(name)
            print(f"  ✅ {png.name}")
    finally:
        server.terminate()
        server.wait(timeout=5)

    print(f"\n🎉 完了: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
