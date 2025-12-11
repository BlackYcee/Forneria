import re

with open('pos/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Agregar import Decimal
if 'from decimal import Decimal' not in content:
    content = content.replace(
        'from django.db import transaction',
        'from decimal import Decimal\nfrom django.db import transaction'
    )

# Cambiar total_acumulado = 0 a Decimal('0')
content = re.sub(
    r'total_acumulado = 0\b',
    "total_acumulado = Decimal('0')",
    content
)

# Cambiar división por float a Decimal
content = content.replace(
    'total_acumulado / 1.19',
    "total_acumulado / Decimal('1.19')"
)

with open('pos/services.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Archivo actualizado correctamente')
