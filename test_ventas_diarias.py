#!/usr/bin/env python
"""
Test del método ventas_diarias
"""
from analytics.services import FinanzasMetrics, _date_to_datetime_range
from pos.models import Venta
from django.db.models.functions import TruncDate
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

# Test 1: Verificar helper
fecha_inicio_dt, fecha_fin_dt = _date_to_datetime_range(None, None)
print(f"Rango por defecto:")
print(f"  Inicio: {fecha_inicio_dt}")
print(f"  Fin: {fecha_fin_dt}")

# Test 2: Contar ventas en ese rango
ventas_count = Venta.objects.filter(
    fecha__gte=fecha_inicio_dt,
    fecha__lt=fecha_fin_dt
).count()
print(f"\nVentas en rango: {ventas_count}")

# Test 3: Ejecutar la query completa
ventas = Venta.objects.filter(
    fecha__gte=fecha_inicio_dt,
    fecha__lt=fecha_fin_dt
).annotate(
    dia=TruncDate('fecha')
).values('dia').annotate(
    total=Sum('total_con_iva'),
    cantidad=Count('id')
).order_by('dia')

print(f"\nResultados de TruncDate:")
print(f"Total grupos: {ventas.count()}")
for v in list(ventas)[:5]:
    print(f"  Dia: {v['dia']}, Total: {v['total']}, Cantidad: {v['cantidad']}")

# Test 4: Ejecutar el método completo
resultado = FinanzasMetrics.ventas_diarias()
print(f"\nResultado del método ventas_diarias():")
print(f"  Labels count: {len(resultado['labels'])}")
print(f"  Totales count: {len(resultado['totales'])}")
if resultado['labels']:
    print(f"  Primeros 3 labels: {resultado['labels'][:3]}")
    print(f"  Primeros 3 totales: {resultado['totales'][:3]}")
