from django import template

register = template.Library()


@register.filter
def peso_chileno(valor):
    return f"${int(valor):,}".replace(",", ".")
