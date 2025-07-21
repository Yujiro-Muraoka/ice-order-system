from django import template

register = template.Library()


@register.filter
def filter_menu(temp_list, menu_name):
    """temp_listから指定メニュー名の合計数量を計算するカスタムフィルタ"""
    try:
        return sum(item['quantity'] for item in temp_list if item['menu'] == menu_name)
    except Exception:
        return 0


@register.filter
def get_item(dictionary, key):
    """辞書から指定キーの値を取得するカスタムフィルタ"""
    return dictionary.get(key)
