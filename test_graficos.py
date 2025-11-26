#!/usr/bin/env python
"""
Test de los 3 gráficos que faltan
"""
from analytics.services import FinanzasMetrics
import json

print("=== TEST VENTAS POR DIA SEMANA ===")
ventas_dia_semana = FinanzasMetrics.ventas_por_dia_semana()
print(f"Labels: {ventas_dia_semana['labels']}")
print(f"Totales: {ventas_dia_semana['totales']}")
print(f"Cantidades: {ventas_dia_semana['cantidades']}")

print("\n=== TEST CLIENTES NUEVOS VS RECURRENTES ===")
clientes_nuevos = FinanzasMetrics.clientes_nuevos_vs_recurrentes()
print(json.dumps(clientes_nuevos, indent=2))

print("\n=== TEST VENTAS POR HORA ===")
ventas_hora = FinanzasMetrics.ventas_por_hora()
print(f"Labels count: {len(ventas_hora['labels'])}")
print(f"Primeras 5 horas: {ventas_hora['labels'][:5]}")
print(f"Primeros 5 totales: {ventas_hora['totales'][:5]}")
print(f"Suma total: {sum(ventas_hora['totales'])}")
