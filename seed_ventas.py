import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Producto, Lote, Cliente, Venta, DetalleVenta, Pago, Empleado

print('\n🌱 Iniciando seed de ventas...\n')

# Actualizar stocks desde lotes
print('📦 Actualizando stocks desde lotes...')
lotes = Lote.objects.all()
for lote in lotes:
    producto = lote.producto
    producto.stock_fisico = lote.stock_inicial
    producto.save()
    print(f'  ✅ {producto.nombre}: {producto.stock_fisico}')

# Obtener datos
productos = list(Producto.objects.all())
clientes = list(Cliente.objects.all()[:10])
empleado = Empleado.objects.first()

print(f'\nProductos: {len(productos)}, Clientes: {len(clientes)}, Empleado: {empleado}\n')

if not productos or not clientes:
    print('❌ No hay productos o clientes')
    exit(1)

# Crear ventas
print('💰 Creando ventas históricas...\n')

ventas_creadas = 0
fechas = [date.today() - timedelta(days=i) for i in range(15, 0, -2)]

for i, cliente in enumerate(clientes):
    fecha_venta = fechas[i % len(fechas)]
    
    # Crear venta
    venta = Venta.objects.create(
        cliente=cliente,
        estado='pagado',
        fecha=fecha_venta
    )
    
    # Agregar 2-4 productos aleatorios
    total_venta = Decimal('0')
    for _ in range(random.randint(2, 4)):
        producto = random.choice(productos)
        cantidad = random.randint(1, 3)
        precio_unitario = Decimal(str(producto.precio_venta))
        
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario
        )
        
        total_venta += precio_unitario * cantidad
    
    # Calcular neto e IVA
    venta.neto = total_venta / Decimal('1.19')
    venta.iva = total_venta - venta.neto
    venta.total = total_venta
    venta.save()
    
    # Crear pago
    Pago.objects.create(
        venta=venta,
        monto=total_venta,
        metodo=random.choice(['EFE', 'TAR', 'TRA'])
    )
    
    ventas_creadas += 1
    print(f'✅ Venta #{venta.id} - {cliente.nombre} - ${total_venta:,.0f}')

print(f'\n📊 Total ventas creadas: {ventas_creadas}')
print('\n✨ ¡Completado!\n')
