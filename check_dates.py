#!/usr/bin/env python
"""
Script para verificar fechas de ventas
"""
from pos.models import Venta
from django.db.models import Min, Max, Count
from django.utils import timezone
from datetime import timedelta

# Estadísticas de fechas
stats = Venta.objects.aggregate(Min('fecha'), Max('fecha'), Count('id'))
print(f"Total ventas: {stats['id__count']}")
print(f"Fecha minima: {stats['fecha__min']}")
print(f"Fecha maxima: {stats['fecha__max']}")

# Verificar últimos 30 días
ahora = timezone.now()
hace_30_dias = ahora - timedelta(days=30)
ventas_30_dias = Venta.objects.filter(fecha__gte=hace_30_dias).count()
print(f"\nVentas ultimos 30 dias: {ventas_30_dias}")

# Primeras 5 ventas
print("\nPrimeras 5 ventas:")
for v in Venta.objects.all()[:5]:
    print(f"  ID: {v.id}, Fecha: {v.fecha}, Total: {v.total_con_iva}")

# Últimas 5 ventas
print("\nUltimas 5 ventas:")
for v in Venta.objects.all().order_by('-fecha')[:5]:
    print(f"  ID: {v.id}, Fecha: {v.fecha}, Total: {v.total_con_iva}")
