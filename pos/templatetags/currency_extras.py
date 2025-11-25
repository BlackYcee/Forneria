from django import template

register = template.Library()

@register.filter
def clp(value):
    """
    Formatea un número como moneda chilena (CLP).
    Ejemplo: 15000 -> $15.000
    """
    try:
        value = float(value)
        return f"${value:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return value
