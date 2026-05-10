from django import template


register = template.Library()


@register.filter
def token_unit(value):
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        return value
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    if number.is_integer():
        return str(int(number))
    return f"{number:.1f}"


@register.filter
def get_item(mapping, key):
    if isinstance(mapping, dict):
        return mapping.get(key)
    return None
