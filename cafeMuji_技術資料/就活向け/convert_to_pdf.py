#!/usr/bin/env python3
"""就活向け概要資料の HTML → PDF 変換（1MB未満を目標）"""

import base64
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MAX_SIZE_BYTES = 1024 * 1024  # 1MB

SCREENSHOTS = [
    "01_login",
    "02_role_select",
    "03_ice_register",
    "04_food_register",
    "05_shavedice_register",
    "06_food_kitchen",
    "07_ice_deshap",
    "08_shavedice_waittime",
]


def find_chrome() -> str | None:
    if Path(CHROME).exists():
        return CHROME
    for name in ("google-chrome", "chromium"):
        result = subprocess.run(["which", name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    return None


def ensure_compressed_images(screenshots_dir: Path) -> Path:
    compressed = screenshots_dir / "compressed"
    compressed.mkdir(parents=True, exist_ok=True)
    for name in SCREENSHOTS:
        png = screenshots_dir / f"{name}.png"
        jpg = compressed / f"{name}.jpg"
        if not png.exists():
            raise FileNotFoundError(f"スクリーンショットが見つかりません: {png}")
        if not jpg.exists() or jpg.stat().st_mtime < png.stat().st_mtime:
            subprocess.run(
                ["magick", str(png), "-resize", "560x", "-strip", "-quality", "45", str(jpg)],
                check=True,
            )
    return compressed


def image_to_data_uri(image_path: Path) -> str:
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{data}"


def embed_screenshot_images(html: str, compressed_dir: Path) -> str:
    """相対パスを base64 に置換し、file:// でも確実に画像が表示されるようにする"""
    for name in SCREENSHOTS:
        jpg = compressed_dir / f"{name}.jpg"
        data_uri = image_to_data_uri(jpg)
        # 元 HTML（png）と、以前のビルド成果物（jpg）の両方に対応
        html = html.replace(f'src="screenshots/{name}.png"', f'src="{data_uri}"')
        html = html.replace(f'src="screenshots/compressed/{name}.jpg"', f'src="{data_uri}"')
        html = html.replace(f'src="screenshots/{name}.jpg"', f'src="{data_uri}"')
    return html


def build_pdf_html(source_html: Path, compressed_dir: Path) -> str:
    html = source_html.read_text(encoding="utf-8")

    html = embed_screenshot_images(html, compressed_dir)

    html = html.replace(
        "background: linear-gradient(135deg, #2c3e2d 0%, #4a6741 100%);",
        "background: #4a6741;",
    )
    html = html.replace(
        'font-family: "SF Mono", "Menlo", "Consolas", monospace;',
        "font-family: 'Noto Sans JP', sans-serif;",
    )
    html = re.sub(
        r"<pre>[\s\S]*?</pre>",
        """<div class="diagram-box">
  <div><strong>cafeMuji 注文管理システム</strong></div>
  <div>フード管理 (food) / アイス管理 (ice) / かき氷管理 (shavedice) / REST API (api)</div>
  <div>Django 5.2 + SQLite / PostgreSQL</div>
  <div>Render.com（クラウドホスティング）</div>
</div>""",
        html,
        count=1,
    )
    html = html.replace('content: "✓";', 'content: "•";')

    font_link = (
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap" rel="stylesheet">'
    )
    html = html.replace(
        "</head>",
        f"{font_link}\n<style>.diagram-box{{background:#f8f9fa;border:1px solid #e0e0e0;border-radius:6px;padding:12px 14px;font-size:9pt;line-height:1.7;margin:8px 0 12px;}}</style>\n</head>",
    )
    html = html.replace(
        'font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", sans-serif;',
        "font-family: 'Noto Sans JP', sans-serif;",
    )

    return html


def render_pdf(chrome: str, html_file: Path, pdf_file: Path) -> None:
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--window-size=794,1123",
        "--force-device-scale-factor=1",
        "--virtual-time-budget=15000",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_file.resolve()}",
        html_file.resolve().as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or not pdf_file.exists():
        raise RuntimeError(result.stderr or "PDF 生成に失敗しました")


def count_pdf_images(pdf_file: Path) -> int:
    import fitz

    doc = fitz.open(pdf_file)
    total = sum(len(doc[i].get_images(full=True)) for i in range(len(doc)))
    doc.close()
    return total


def compress_pdf_if_needed(pdf_file: Path) -> int:
    size = pdf_file.stat().st_size
    if size < MAX_SIZE_BYTES:
        return size

    import fitz

    tmp = pdf_file.with_name("_compressed.pdf")
    doc = fitz.open(pdf_file)
    doc.rewrite_images(dpi_threshold=200, dpi_target=96, quality=45, lossy=True, lossless=False)
    doc.save(tmp, garbage=4, deflate=True, clean=True)
    doc.close()

    if tmp.stat().st_size < size:
        tmp.replace(pdf_file)
        size = pdf_file.stat().st_size
    else:
        tmp.unlink(missing_ok=True)

    return size


def main() -> int:
    base_dir = Path(__file__).parent
    source_html = base_dir / "プロジェクト概要_面接用.html"
    build_html = base_dir / "_pdf_build.html"
    pdf_file = base_dir / "プロジェクト概要_面接用.pdf"

    chrome = find_chrome()
    if not chrome:
        print("❌ Chrome / Chromium が見つかりません。")
        return 1
    if not source_html.exists():
        print(f"❌ HTML ファイルが見つかりません: {source_html}")
        return 1

    print("🚀 PDF 変換を開始します...")
    compressed_dir = ensure_compressed_images(base_dir / "screenshots")
    build_html.write_text(build_pdf_html(source_html, compressed_dir), encoding="utf-8")
    render_pdf(chrome, build_html, pdf_file)

    image_count = count_pdf_images(pdf_file)
    print(f"   埋め込み画像数: {image_count}")
    if image_count < len(SCREENSHOTS):
        print("❌ 画面イメージが PDF に埋め込まれていません。")
        return 1

    size = pdf_file.stat().st_size
    print(f"✅ PDF を作成しました: {pdf_file}")
    print(f"   ファイルサイズ: {size / 1024:.1f} KB")

    if size >= MAX_SIZE_BYTES:
        print("⚠️  1MB を超えています。追加圧縮を試みます...")
        try:
            size = compress_pdf_if_needed(pdf_file)
            image_count = count_pdf_images(pdf_file)
            print(f"   圧縮後: {size / 1024:.1f} KB（画像数: {image_count}）")
        except Exception as exc:
            print(f"   追加圧縮をスキップ: {exc}")

    if count_pdf_images(pdf_file) < len(SCREENSHOTS):
        print("❌ 圧縮後に画像が失われました。")
        return 1

    if size >= MAX_SIZE_BYTES:
        print("❌ 1MB 未満にできませんでした。")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
