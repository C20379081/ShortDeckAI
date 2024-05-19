from django import template
from django.templatetags.static import static

register = template.Library()

#created for displaying the manage profile avatars
@register.filter
def avatar_url(filename):
    return static(f'images/avatars/{filename}')
