from django import template

register = template.Library()

@register.filter
def add_comma(value):
    """Adds commas to large numbers for better readability."""
    try:
        return '{:,}'.format(int(value))
    except (ValueError, TypeError):
        return value  # If it's not a valid number, return the original value