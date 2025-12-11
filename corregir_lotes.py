"""
Script para corregir lotes existentes que tienen stock_actual=0
Copia el valor de stock_inicial a stock_actual
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forneria.settings')
django.setup()

from pos.models import Lote

print('🔄 Corrigiendo lotes con stock_actual=0...\n')

# Buscar todos los lotes con stock_actual=0
lotes_a_corregir = Lote.objects.filter(stock_actual=0)
total = lotes_a_corregir.count()

if total == 0:
    print('✅ No hay lotes con stock_actual=0. Todo está correcto.')
else:
    print(f'📋 Se encontraron {total} lotes con stock_actual=0\n')
    
    corregidos = 0
    for lote in lotes_a_corregir:
        print(f'  🔧 Lote {lote.numero_lote} ({lote.producto.nombre})')
        print(f'      Antes: stock_inicial={lote.stock_inicial}, stock_actual={lote.stock_actual}')
        
        lote.stock_actual = lote.stock_inicial
        lote.save(update_fields=['stock_actual'])
        corregidos += 1
        
        print(f'      Después: stock_inicial={lote.stock_inicial}, stock_actual={lote.stock_actual}')
        print()
    
    print(f'{"="*60}')
    print(f'✅ {corregidos} lotes corregidos exitosamente')
    print(f'{"="*60}')
