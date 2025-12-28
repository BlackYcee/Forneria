from pos.models import Venta, Pago, DetalleVenta

print("\n📋 Verificar ventas en DB:\n")

ventas = Venta.objects.all()
print(f"Total ventas: {ventas.count()}\n")

for venta in ventas:
    print(f"Venta #{venta.id}:")
    print(f"  Cliente: {venta.cliente.nombre if venta.cliente else 'Sin cliente'}")
    print(f"  Total: {venta.total}")
    print(f"  Estado: {venta.estado}")
    print()
