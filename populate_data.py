"""
Script para poblar la base de datos con datos de prueba
Ejecutar: python populate_data.py
"""
import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from django.utils import timezone
from pos.models import Categoria, Producto, Lote, Cliente, Venta, DetalleVenta

print(">>> Iniciando poblacion de datos de prueba...")

# Limpiar datos existentes (opcional)
print("\n>>> Limpiando datos antiguos...")
DetalleVenta.objects.all().delete()
Venta.objects.all().delete()
Cliente.objects.all().delete()
Lote.objects.all().delete()
Producto.objects.all().delete()
Categoria.objects.all().delete()

# 1. Crear Categorías
print("\n>>> Creando categorias...")
categorias_data = [
    {"nombre": "Panadería", "descripcion": "Panes artesanales y especiales"},
    {"nombre": "Pastelería", "descripcion": "Tortas, pasteles y postres"},
    {"nombre": "Bebidas", "descripcion": "Bebidas frías y calientes"},
    {"nombre": "Snacks", "descripcion": "Galletas, alfajores y bocadillos"},
]

categorias = {}
for cat_data in categorias_data:
    cat = Categoria.objects.create(**cat_data)
    categorias[cat.nombre] = cat
    print(f"  [OK] {cat.nombre}")

# 2. Crear Productos con Lotes
print("\n>>> Creando productos...")
productos_data = [
    # Panadería
    {"nombre": "Pan Integral", "categoria": "Panadería", "precio": 2500, "stock": 120},
    {"nombre": "Pan Francés", "categoria": "Panadería", "precio": 1800, "stock": 150},
    {"nombre": "Hallulla", "categoria": "Panadería", "precio": 1200, "stock": 200},
    {"nombre": "Marraqueta", "categoria": "Panadería", "precio": 1500, "stock": 180},
    {"nombre": "Pan de Masa Madre", "categoria": "Panadería", "precio": 3500, "stock": 80},

    # Pastelería
    {"nombre": "Torta Chocolate", "categoria": "Pastelería", "precio": 15000, "stock": 25},
    {"nombre": "Kuchen de Frambuesa", "categoria": "Pastelería", "precio": 8500, "stock": 30},
    {"nombre": "Cheesecake", "categoria": "Pastelería", "precio": 12000, "stock": 20},
    {"nombre": "Alfajor de Chocolate", "categoria": "Pastelería", "precio": 1500, "stock": 100},

    # Bebidas
    {"nombre": "Café Americano", "categoria": "Bebidas", "precio": 2000, "stock": 500},
    {"nombre": "Café Latte", "categoria": "Bebidas", "precio": 2800, "stock": 500},
    {"nombre": "Jugo Natural Naranja", "categoria": "Bebidas", "precio": 3000, "stock": 80},

    # Snacks
    {"nombre": "Galletas de Avena", "categoria": "Snacks", "precio": 2500, "stock": 150},
    {"nombre": "Empanada de Queso", "categoria": "Snacks", "precio": 1800, "stock": 100},
    {"nombre": "Croissant", "categoria": "Snacks", "precio": 2200, "stock": 90},
]

productos = []
for idx, prod_data in enumerate(productos_data, start=1):
    cat_nombre = prod_data.pop("categoria")
    stock = prod_data.pop("stock")

    # Generar código de barra único (formato EAN-13 simplificado)
    codigo_barra = 7800000000000 + idx * 100

    producto = Producto.objects.create(
        nombre=prod_data["nombre"],
        codigo_barra=codigo_barra,
        precio=prod_data["precio"],
        marca="Forneria Artesanal",
        descripcion=f"{prod_data['nombre']} elaborado con ingredientes de primera calidad",
        tipo="Alimento",
        presentacion="Unidad",
        formato="Individual",
        categoria=categorias[cat_nombre]
    )

    # Crear lote para el producto
    Lote.objects.create(
        producto=producto,
        numero_lote=f"L{producto.id:04d}-2025",
        fecha_elaboracion=timezone.now().date() - timedelta(days=2),
        fecha_caducidad=timezone.now().date() + timedelta(days=15),
        stock_actual=stock,
        stock_minimo=10,
        stock_maximo=stock + 50
    )

    productos.append(producto)
    print(f"  [OK] {producto.nombre} - CB: {codigo_barra} - ${producto.precio} (Stock: {stock})")

# 3. Crear Clientes
print("\n>>> Creando clientes...")
clientes_data = [
    {"rut": "12345678-9", "nombre": "Juan Pérez González", "correo": "juan.perez@email.com"},
    {"rut": "23456789-0", "nombre": "María López Silva", "correo": "maria.lopez@email.com"},
    {"rut": "34567890-1", "nombre": "Carlos Ramírez", "correo": "carlos.ramirez@email.com"},
    {"rut": "45678901-2", "nombre": "Ana Martínez", "correo": "ana.martinez@email.com"},
    {"rut": "56789012-3", "nombre": "Pedro Soto", "correo": "pedro.soto@email.com"},
    {"rut": "67890123-4", "nombre": "Laura Fernández", "correo": "laura.fernandez@email.com"},
    {"rut": "78901234-5", "nombre": "Diego Torres", "correo": "diego.torres@email.com"},
]

clientes = []
for cliente_data in clientes_data:
    cliente = Cliente.objects.create(**cliente_data)
    clientes.append(cliente)
    print(f"  [OK] {cliente.nombre}")

# 4. Crear Ventas (últimos 30 días)
print("\n>>> Creando ventas de los ultimos 30 dias...")

# Función para generar ventas realistas
def generar_venta(fecha, cliente=None):
    # Cantidad de productos por venta (1-5)
    num_productos = random.randint(1, 5)
    productos_venta = random.sample(productos, min(num_productos, len(productos)))

    # Canal de venta
    canal = random.choice(['presencial', 'presencial', 'presencial', 'delivery'])  # 75% presencial

    # Calcular totales
    subtotal = Decimal('0')
    detalles_data = []

    for producto in productos_venta:
        cantidad = random.randint(1, 3)
        precio_unitario = producto.precio
        descuento_pct = random.choice([0, 0, 0, 5, 10])  # Mayoría sin descuento

        linea_total = precio_unitario * cantidad
        descuento_linea = (linea_total * Decimal(descuento_pct) / Decimal('100'))
        subtotal += linea_total - descuento_linea

        detalles_data.append({
            'producto': producto,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'descuento_pct': descuento_pct
        })

    total_sin_iva = subtotal
    total_iva = (total_sin_iva * Decimal('0.19')).quantize(Decimal('0.01'))
    total_con_iva = total_sin_iva + total_iva
    descuento_total = sum((d['precio_unitario'] * d['cantidad'] * Decimal(d['descuento_pct']) / Decimal('100')) for d in detalles_data)

    # Crear venta
    venta = Venta.objects.create(
        fecha=fecha,
        total_sin_iva=total_sin_iva,
        total_iva=total_iva,
        descuento=descuento_total.quantize(Decimal('0.01')),
        total_con_iva=total_con_iva,
        canal_venta=canal,
        folio=f"V{random.randint(1000, 9999)}",
        cliente=cliente
    )

    # Crear detalles
    for detalle_data in detalles_data:
        DetalleVenta.objects.create(
            venta=venta,
            producto=detalle_data['producto'],
            cantidad=detalle_data['cantidad'],
            precio_unitario=detalle_data['precio_unitario'],
            descuento_pct=detalle_data['descuento_pct']
        )

    return venta

# Generar ventas para los últimos 30 días
ventas_creadas = 0
hoy = timezone.now()

for dias_atras in range(30, -1, -1):
    fecha_venta = hoy - timedelta(days=dias_atras)

    # Más ventas en días recientes y fines de semana
    if dias_atras <= 7:
        num_ventas = random.randint(8, 15)  # Última semana
    elif fecha_venta.weekday() >= 5:  # Sábado o Domingo
        num_ventas = random.randint(12, 20)
    else:
        num_ventas = random.randint(5, 10)

    for _ in range(num_ventas):
        # Distribuir ventas a lo largo del día
        hora = random.randint(8, 20)
        minuto = random.randint(0, 59)
        fecha_hora = fecha_venta.replace(hour=hora, minute=minuto)

        # 60% de ventas con cliente, 40% sin cliente
        cliente = random.choice(clientes) if random.random() < 0.6 else None

        generar_venta(fecha_hora, cliente)
        ventas_creadas += 1

    print(f"  [OK] Dia {fecha_venta.strftime('%d/%m/%Y')}: {num_ventas} ventas")

print(f"\n>>> Poblacion completada!")
print(f"  Categorias: {Categoria.objects.count()}")
print(f"  Productos: {Producto.objects.count()}")
print(f"  Clientes: {Cliente.objects.count()}")
print(f"  Ventas: {Venta.objects.count()}")
print(f"  Detalles de venta: {DetalleVenta.objects.count()}")
print(f"\n>>> Datos de prueba creados exitosamente!")
print(f"\n>>> Ahora abre: http://127.0.0.1:8000/analytics/dashboard/")
