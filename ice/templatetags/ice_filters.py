from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """辞書から指定キーの値を取得するカスタムフィルタ"""
    try:
        return dictionary.get(key)
    except Exception:
        return None


@register.filter
def to(value, end):
    """指定値からendまでのrangeを返すカスタムフィルタ"""
    try:
        return range(int(value), int(end))
    except Exception:
        return range(0)


