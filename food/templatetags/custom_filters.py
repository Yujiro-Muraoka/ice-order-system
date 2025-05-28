from django import template

register = template.Library()

@register.filter
def filter_menu(temp_list, menu_name):
    try:
        return sum(item['quantity'] for item in temp_list if item['menu'] == menu_name)
    except Exception:
        return 0
