"""
Script para insertar productos desde el CSV a la base de datos SQLite.
Ejecutar: python insertar_productos.py
"""
import os
import sys
import django
import csv
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Categoria, Producto, Lote

def insertar_productos():
    csv_path = os.path.join('pos', 'fixtures', 'forneria_products_extracted_from_pdf.csv')
    
    if not os.path.exists(csv_path):
        print(f'❌ CSV no encontrado: {csv_path}')
        return
    
    print('🔄 Insertando productos desde CSV...\n')
    
    productos_created = 0
    lotes_created = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Obtener o crear categoría
            categoria, cat_created = Categoria.objects.get_or_create(
                nombre=row['categoria'],
                defaults={'descripcion': f'Categoría {row["categoria"]}'}
            )
            
            if cat_created:
                print(f'  ➕ Categoría creada: {categoria.nombre}')
            
            # Crear producto si no existe
            producto, created = Producto.objects.get_or_create(
                nombre=row['nombre'],
                defaults={
                    'descripcion': row['descripcion'],
                    'categoria': categoria,
                    'precio_venta': Decimal(row['precio']),
                    'stock_minimo_global': 5,
                    'marca': 'La Fornería',
                    'tipo': row['tipo'],
                    'presentacion': row['presentacion'],
                }
            )
            
            if created:
                productos_created += 1
                print(f'  ✅ Producto: {producto.nombre} (${producto.precio_venta})')
                
                # Crear lote inicial para el producto
                fecha_caducidad = date.today() + timedelta(days=int(row['caducidad_days']))
                lote = Lote.objects.create(
                    producto=producto,
                    numero_lote=f'INIT-{producto.id:04d}',
                    stock_inicial=int(row['stock']),
                    stock_actual=int(row['stock']),
                    precio_costo_unitario=Decimal(row['costo_unitario']),
                    fecha_caducidad=fecha_caducidad,
                )
                lotes_created += 1
            else:
                print(f'  ⚠️  Ya existe: {producto.nombre}')
    
    print(f'\n{"="*50}')
    print(f'✅ Productos insertados: {productos_created}')
    print(f'✅ Lotes creados: {lotes_created}')
    print(f'📊 Total categorías: {Categoria.objects.count()}')
    print(f'📦 Total productos: {Producto.objects.count()}')
    print(f'📋 Total lotes: {Lote.objects.count()}')
    print(f'{"="*50}')

if __name__ == '__main__':
    insertar_productos()
