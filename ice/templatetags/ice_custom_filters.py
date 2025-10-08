from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """辞書から指定キーの値を取得するカスタムフィルタ"""
    return dictionary.get(key)


@register.filter
def to(value, end):
    """指定値からendまでのrangeを返すカスタムフィルタ"""
    return range(value, end)