"""
cafeMuji - エラーハンドリング機能
共通エラーハンドラとログ機能

このファイルは、アプリケーション全体で使用する
エラーハンドリング機能を提供します。
"""

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from functools import wraps

# ロガーの設定
logger = logging.getLogger('cafeMuji')


def handle_errors(func):
    """
    ビュー関数用のエラーハンドリングデコレータ
    
    使用例:
    @handle_errors
    def my_view(request):
        # ビュー処理
        pass
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except ValueError as e:
            logger.error(f"ValueError in {func.__name__}: {str(e)}")
            if request.is_ajax():
                return JsonResponse({
                    'error': True,
                    'message': '入力値に問題があります。'
                }, status=400)
            return render(request, 'common/error.html', {
                'error_message': '入力値に問題があります。'
            })
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            if request.is_ajax():
                return JsonResponse({
                    'error': True,
                    'message': 'システムエラーが発生しました。'
                }, status=500)
            return render(request, 'common/error.html', {
                'error_message': 'システムエラーが発生しました。'
            })
    return wrapper


def log_user_action(action_type, user_info=None, additional_info=None):
    """
    ユーザーアクションのログ記録
    
    Args:
        action_type (str): アクションの種類
        user_info (str): ユーザー情報
        additional_info (dict): 追加情報
    """
    log_message = f"Action: {action_type}"
    if user_info:
        log_message += f" | User: {user_info}"
    if additional_info:
        log_message += f" | Info: {additional_info}"
    
    logger.info(log_message)


def log_database_operation(operation_type, model_name, record_id=None, details=None):
    """
    データベース操作のログ記録
    
    Args:
        operation_type (str): 操作の種類（CREATE, UPDATE, DELETE等）
        model_name (str): モデル名
        record_id (int): レコードID
        details (dict): 操作の詳細
    """
    log_message = f"DB {operation_type}: {model_name}"
    if record_id:
        log_message += f" (ID: {record_id})"
    if details:
        log_message += f" | Details: {details}"
    
    logger.info(log_message)


class PerformanceMonitor:
    """
    パフォーマンス監視クラス
    """
    
    @staticmethod
    def log_slow_query(query_time, query_info):
        """
        遅いクエリのログ記録
        
        Args:
            query_time (float): クエリ実行時間（秒）
            query_info (str): クエリ情報
        """
        if query_time > 1.0:  # 1秒以上のクエリを記録
            logger.warning(f"Slow query detected: {query_time:.2f}s | {query_info}")
    
    @staticmethod
    def log_memory_usage(memory_mb, context=None):
        """
        メモリ使用量のログ記録
        
        Args:
            memory_mb (float): メモリ使用量（MB）
            context (str): 使用状況
        """
        if memory_mb > 100:  # 100MB以上の使用量を記録
            logger.warning(f"High memory usage: {memory_mb:.1f}MB | Context: {context}")


def validate_order_data(order_data, required_fields):
    """
    注文データの検証
    
    Args:
        order_data (dict): 注文データ
        required_fields (list): 必須フィールドのリスト
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # 必須フィールドのチェック
        for field in required_fields:
            if field not in order_data or not order_data[field]:
                return False, f"必須フィールド '{field}' が不足しています。"
        
        # データ型の検証
        if 'quantity' in order_data:
            try:
                quantity = int(order_data['quantity'])
                if quantity <= 0:
                    return False, "数量は1以上である必要があります。"
            except (ValueError, TypeError):
                return False, "数量は数値である必要があります。"
        
        if 'clip_number' in order_data:
            try:
                clip_number = int(order_data['clip_number'])
                if clip_number < 0 or clip_number > 16:
                    return False, "クリップ番号は0-16の範囲である必要があります。"
            except (ValueError, TypeError):
                return False, "クリップ番号は数値である必要があります。"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, "データ検証中にエラーが発生しました。"


# 共通エラーレスポンス
ERROR_RESPONSES = {
    'invalid_data': {
        'error': True,
        'message': '入力データが無効です。',
        'code': 'INVALID_DATA'
    },
    'not_found': {
        'error': True,
        'message': '指定されたデータが見つかりません。',
        'code': 'NOT_FOUND'
    },
    'database_error': {
        'error': True,
        'message': 'データベースエラーが発生しました。',
        'code': 'DATABASE_ERROR'
    },
    'permission_denied': {
        'error': True,
        'message': '権限がありません。',
        'code': 'PERMISSION_DENIED'
    }
}