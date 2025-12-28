import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Producto, Lote

# Buscar productos sin lotes pero con stock_fisico > 0
productos_sin_lotes = []
for p in Producto.objects.all():
    if p.stock_fisico > 0 and p.lotes.filter(eliminado__isnull=True).count() == 0:
        productos_sin_lotes.append(p)

print(f'\n=== Productos con stock_fisico > 0 pero SIN lotes ===')
print(f'Total encontrados: {len(productos_sin_lotes)}\n')

for p in productos_sin_lotes:
    print(f'- {p.nombre} (ID {p.id}): stock_fisico={p.stock_fisico}')
    
    # Crear lote inicial
    fecha_caducidad = date.today() + timedelta(days=90)
    lote = Lote.objects.create(
        producto=p,
        numero_lote=f'INIT-{p.id}',
        fecha_elaboracion=date.today(),
        fecha_caducidad=fecha_caducidad,
        precio_costo_unitario=p.costo_unitario or 0,
        stock_inicial=p.stock_fisico,
        stock_actual=p.stock_fisico
    )
    print(f'  ✅ Lote creado: {lote.numero_lote} con {lote.stock_actual} unidades\n')

print(f'\n✅ Proceso completado. {len(productos_sin_lotes)} lotes creados.')
