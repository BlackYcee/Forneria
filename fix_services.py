#!/usr/bin/env python
"""
Script temporal para actualizar services.py
Reemplaza fecha__date__range con llamadas al helper _date_to_datetime_range
"""

with open('analytics/services.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Lista de métodos a actualizar
updates = [
    # productos_top
    {
        'old': '''    @staticmethod
    def productos_top(limite=10, fecha_inicio=None, fecha_fin=None):
        """
        Top productos más vendidos por cantidad y por ingresos
        """
        filtros = Q()
        if fecha_inicio and fecha_fin:
            filtros = Q(venta__fecha__date__range=[fecha_inicio, fecha_fin])''',
        'new': '''    @staticmethod
    def productos_top(limite=10, fecha_inicio=None, fecha_fin=None):
        """
        Top productos más vendidos por cantidad y por ingresos
        """
        fecha_inicio_dt, fecha_fin_dt = _date_to_datetime_range(fecha_inicio, fecha_fin)
        filtros = Q(venta__fecha__gte=fecha_inicio_dt, venta__fecha__lt=fecha_fin_dt)'''
    },
    # ventas_por_categoria
    {
        'old': '''    @staticmethod
    def ventas_por_categoria(fecha_inicio=None, fecha_fin=None):
        """
        Distribución de ventas por categoría de producto
        Para gráfico de dona/pie
        """
        filtros = Q()
        if fecha_inicio and fecha_fin:
            filtros = Q(venta__fecha__date__range=[fecha_inicio, fecha_fin])''',
        'new': '''    @staticmethod
    def ventas_por_categoria(fecha_inicio=None, fecha_fin=None):
        """
        Distribución de ventas por categoría de producto
        Para gráfico de dona/pie
        """
        fecha_inicio_dt, fecha_fin_dt = _date_to_datetime_range(fecha_inicio, fecha_fin)
        filtros = Q(venta__fecha__gte=fecha_inicio_dt, venta__fecha__lt=fecha_fin_dt)'''
    },
    # ventas_por_canal
    {
        'old': '''        ventas_canal = Venta.objects.filter(
            fecha__date__range=[fecha_inicio, fecha_fin]
        ).values('canal_venta')''',
        'new': '''        ventas_canal = Venta.objects.filter(
            fecha__gte=fecha_inicio_dt,
            fecha__lt=fecha_fin_dt
        ).values('canal_venta')'''
    },
]

for update in updates:
    content = content.replace(update['old'], update['new'])

# Escribir de vuelta
with open('analytics/services.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ services.py actualizado")
