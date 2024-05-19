from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def get_playstyle(vpip):
    try:
        vpip_value = float(vpip)
    except ValueError:
        return mark_safe("Invalid VPIP value")
    
    if vpip_value < 25.0:
        return 'Tight'
    elif vpip_value < 35.0:
        return 'Moderately Tight'
    elif vpip_value < 50.0:
        return 'Loose'
    else:
        return 'Very Loose'

@register.filter
def get_aggression(pfr):
    print(pfr)
    try:
        pfr_value = float(pfr)
    except ValueError:
        return mark_safe("Invalid PFR value")
    
    if pfr_value < 10.0:
        return 'Passive'
    elif pfr_value < 15.0:
        return 'Moderately Passive'
    elif pfr_value < 25.0:
        return 'Aggressive'
    else:
        return 'Very Aggressive'

