#!/usr/bin/env python
"""Script para agregar campos delivery al VentaInputSerializer"""
import re

filepath = 'pos/serializers.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar la clase VentaInputSerializer y agregar los campos después de 'canal'
patron = r"(class VentaInputSerializer\(serializers\.Serializer\):.*?canal = serializers\.CharField\(max_length=10, required=False\))"

reemplazo = r"""\1
    # Campos adicionales para Delivery
    direccion_entrega = serializers.CharField(max_length=255, required=False, allow_blank=True)
    referencias = serializers.CharField(max_length=255, required=False, allow_blank=True)
    instrucciones = serializers.CharField(max_length=500, required=False, allow_blank=True)
    cliente_nombre = serializers.CharField(max_length=150, required=False, allow_blank=True)
    cliente_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    cliente_email = serializers.EmailField(required=False, allow_blank=True)"""

content_nuevo = re.sub(patron, reemplazo, content, flags=re.DOTALL)

if content != content_nuevo:
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_nuevo)
    print("✅ Campos de delivery agregados exitosamente")
else:
    print("⚠️ No se encontró el patrón esperado en serializers.py")
