from django import template

register = template.Library()

@register.filter
def get_item(value, arg):
    return value[arg]
