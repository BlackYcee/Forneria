from django import template

register = template.Library()


@register.filter(name='clp')
def clp(value):
    """Formatea un número como peso chileno sin decimales, con separador de miles '.'

    Ejemplo: 1200.0 -> "$1.200"
    Si el valor no es numérico, lo devuelve tal cual.
    """
    try:
        val = float(value)
    except (TypeError, ValueError):
        return value
    # Redondear al entero más cercano (CLP no usa centavos normalmente)
    int_val = int(round(val))
    # Formateo con separador de miles '.'
    s = "{:,}".format(int_val).replace(",", ".")
    return f"${s}"
