import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Producto, Lote
from django.db.models import Sum

p = Producto.objects.get(nombre__icontains='Pastas Italianas')
lotes = Lote.objects.filter(producto=p, eliminado__isnull=True)
print(f'\n=== Producto: {p.nombre} (ID {p.id}) ===')
print(f'stock_fisico registrado: {p.stock_fisico}')
print(f'Lotes encontrados: {lotes.count()}\n')
for lote in lotes:
    print(f'Lote #{lote.id} - {lote.numero_lote}')
    print(f'  stock_inicial: {lote.stock_inicial}')
    print(f'  stock_actual: {lote.stock_actual}')
    print(f'  fecha_caducidad: {lote.fecha_caducidad}\n')
    
suma = lotes.aggregate(total=Sum('stock_actual'))['total'] or 0
print(f'Suma de stock_actual en lotes: {suma}')
print(f'Diferencia (stock_fisico - suma lotes): {p.stock_fisico - suma}\n')
