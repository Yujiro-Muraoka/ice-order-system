#!/usr/bin/env python3
"""
HTMLファイルをPDFに変換するスクリプト
cafeMuji技術資料のHTMLファイルをPDFに変換します
"""

import os
import subprocess
import sys
from pathlib import Path

def convert_html_to_pdf(html_file, pdf_file):
    """HTMLファイルをPDFに変換"""
    try:
        # Chrome/Chromiumを使用してPDF変換
        cmd = [
            'google-chrome',
            '--headless',
            '--disable-gpu',
            '--print-to-pdf=' + pdf_file,
            '--print-to-pdf-no-header',
            html_file
        ]
        
        # macOSの場合はChromeのパスを調整
        if sys.platform == 'darwin':
            cmd[0] = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {html_file} → {pdf_file}")
            return True
        else:
            print(f"❌ {html_file} の変換に失敗: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Chromeが見つかりません: {html_file}")
        return False
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 cafeMuji技術資料のHTML→PDF変換を開始します...")
    
    # 現在のディレクトリ
    current_dir = Path('.')
    
    # HTMLファイルの一覧
    html_files = [
        'README.html',
        'システム概要説明書.html',
        '技術仕様書.html',
        'データベース設計書.html',
        '画面遷移図.html',
        'デプロイ手順書.html',
        '運用マニュアル.html'
    ]
    
    # 変換結果
    success_count = 0
    total_count = len(html_files)
    
    for html_file in html_files:
        if html_file in html_files:
            pdf_file = html_file.replace('.html', '.pdf')
            
            if convert_html_to_pdf(html_file, pdf_file):
                success_count += 1
    
    print(f"\n📊 変換完了: {success_count}/{total_count} ファイル")
    
    if success_count == total_count:
        print("🎉 全てのファイルの変換が完了しました！")
    else:
        print("⚠️ 一部のファイルの変換に失敗しました。")
        print("手動でブラウザからPDFとして保存してください。")

if __name__ == "__main__":
    main()
