from django.shortcuts import render, redirect
from django.contrib import messages

# 共通パスコード（必要に応じて環境変数等で管理してください）
SHARED_PASSCODE = "1234"

def login_view(request):
    """
    ログイン画面（共通認証ビュー）
    - POST: パスコード認証
    - GET: ログインフォーム表示
    """
    if request.method == 'POST':
        code = request.POST.get('passcode')
        if code == SHARED_PASSCODE:
            request.session['logged_in'] = True
            return redirect('/')
        else:
            messages.error(request, "パスコードが間違っています")
    
    return render(request, 'common/login.html')

def logout_view(request):
    """
    ログアウト処理（共通認証ビュー）
    - セッションを破棄し、ログイン画面へリダイレクト
    """
    request.session.flush()
    return redirect('/login') 