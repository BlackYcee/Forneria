import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Producto, Lote, Cliente, Venta, DetalleVenta, Pago, Empleado

print('\n🌱 Iniciando seed completo de ventas...\n')

# 1. Actualizar stocks
print('📦 Actualizando stocks desde lotes...')
lotes = Lote.objects.all()
for lote in lotes:
    producto = lote.producto
    producto.stock_fisico = lote.stock_inicial
    producto.save()
print(f'✅ {lotes.count()} productos actualizados\n')

# 2. Crear clientes si no existen
print('👥 Verificando clientes...')
clientes_datos = [
    {'rut': '12345678-9', 'nombre': 'Juan', 'apellido': 'Pérez', 'email': 'juan@email.com', 'telefono': '912345678', 'direccion': 'Los Arrayanes 1234'},
    {'rut': '23456789-0', 'nombre': 'María', 'apellido': 'García', 'email': 'maria@email.com', 'telefono': '923456789', 'direccion': 'Av. Francisco 567'},
    {'rut': '34567890-1', 'nombre': 'Carlos', 'apellido': 'López', 'email': 'carlos@email.com', 'telefono': '934567890', 'direccion': 'Av. del Mar 2890'},
    {'rut': '45678901-2', 'nombre': 'Ana', 'apellido': 'Fernández', 'email': 'ana@email.com', 'telefono': '945678901', 'direccion': 'Calle Balmaceda 1456'},
    {'rut': '56789012-3', 'nombre': 'Roberto', 'apellido': 'Martínez', 'email': 'roberto@email.com', 'telefono': '956789012', 'direccion': 'Peñuelas 3456'},
    {'rut': '67890123-4', 'nombre': 'Carmen', 'apellido': 'Sánchez', 'email': 'carmen@email.com', 'telefono': '967890123', 'direccion': 'Los Carrera 789'},
    {'rut': '78901234-5', 'nombre': 'Pedro', 'apellido': 'Ramírez', 'email': 'pedro@email.com', 'telefono': '978901234', 'direccion': 'Matta 4567'},
    {'rut': '89012345-6', 'nombre': 'Isabel', 'apellido': 'Flores', 'email': 'isabel@email.com', 'telefono': '989012345', 'direccion': 'Infante 234'},
    {'rut': '90123456-7', 'nombre': 'Diego', 'apellido': 'Morales', 'email': 'diego@email.com', 'telefono': '990123456', 'direccion': 'Av. Cisternas 5678'},
    {'rut': '11223344-5', 'nombre': 'Patricia', 'apellido': 'Vega', 'email': 'patricia@email.com', 'telefono': '911223344', 'direccion': 'Av. Cuatro Esquinas 1123'},
]

clientes = []
for cd in clientes_datos:
    c, created = Cliente.objects.get_or_create(rut=cd['rut'], defaults=cd)
    if created:
        print(f'  ✅ {c.nombre} creado')
    clientes.append(c)

print(f'✅ Total clientes: {len(clientes)}\n')

# 3. Obtener datos
productos = list(Producto.objects.filter(stock_fisico__gt=0))
empleado = Empleado.objects.first()

print(f'📊 Productos con stock: {len(productos)}, Empleado: {empleado}\n')

if not productos or not clientes:
    print('❌ No hay productos o clientes')
    exit(1)

# 4. Crear ventas
print('💰 Creando ventas históricas...\n')

ventas_creadas = 0
fechas = [date.today() - timedelta(days=i) for i in range(15, 0, -2)]

# Limpiar ventas previas si existen
print('🗑️  Limpiando ventas previas...')
Venta.objects.all().delete()
print('✅ Limpias\n')

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
    num_items = random.randint(2, 4)
    
    for _ in range(num_items):
        producto = random.choice(productos)
        cantidad = random.randint(1, 3)
        precio_unitario = Decimal(str(producto.precio_venta)) if producto.precio_venta else Decimal('5000')
        
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
print('✨ ¡Completado!\n')
