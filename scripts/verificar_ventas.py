#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Venta, Pago, DetalleVenta

print("\n📋 Verificar ventas en DB:\n")

ventas = Venta.objects.all()
print(f"Total ventas: {ventas.count()}\n")

for venta in ventas:
    print(f"Venta #{venta.id}:")
    print(f"  Cliente: {venta.cliente.nombre if venta.cliente else 'Sin cliente'}")
    print(f"  Fecha: {venta.fecha}")
    print(f"  Total: {venta.total}")
    print(f"  Estado: {venta.estado}")
    
    detalles = DetalleVenta.objects.filter(venta=venta)
    print(f"  Detalles: {detalles.count()}")
    for det in detalles:
        print(f"    - {det.producto.nombre} x{det.cantidad} @ {det.precio_unitario}")
    
    pagos = Pago.objects.filter(venta=venta)
    print(f"  Pagos: {pagos.count()}")
    for pago in pagos:
        print(f"    - {pago.metodo}: {pago.monto}")
    print()
