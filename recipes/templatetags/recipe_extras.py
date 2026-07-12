import zlib

from django import template

register = template.Library()

# recipe_category is free text, not a fixed choice list, so the tab color is
# hashed from the category string rather than looked up in a maintained
# mapping — any category gets a stable, deterministic color.
_TAB_CLASSES = ["tab-red", "tab-blue", "tab-gold", "tab-green"]


@register.filter
def tab_class(category):
    if not category:
        return _TAB_CLASSES[0]
    index = zlib.crc32(category.strip().lower().encode()) % len(_TAB_CLASSES)
    return _TAB_CLASSES[index]


@register.filter
def stars(rating):
    if not rating:
        return "—"
    return "★" * rating + "☆" * (5 - rating)
