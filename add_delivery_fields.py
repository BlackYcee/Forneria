import sys

# Leer el archivo
with open('pos/serializers.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea "canal = serializers.CharField..."
insert_index = None
for i, line in enumerate(lines):
    if 'canal = serializers.CharField(max_length=10, required=False)' in line:
        insert_index = i + 1
        break

if insert_index:
    # Crear las nuevas líneas
    new_lines = [
        "    # Campos adicionales para Delivery\n",
        "    direccion_entrega = serializers.CharField(max_length=255, required=False, allow_blank=True)\n",
        "    referencias = serializers.CharField(max_length=255, required=False, allow_blank=True)\n",
        "    instrucciones = serializers.CharField(max_length=500, required=False, allow_blank=True)\n",
        "    cliente_nombre = serializers.CharField(max_length=150, required=False, allow_blank=True)\n",
        "    cliente_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)\n",
        "    cliente_email = serializers.EmailField(required=False, allow_blank=True)\n",
    ]
    
    # Insertar las líneas
    lines = lines[:insert_index] + new_lines + lines[insert_index:]
    
    # Escribir el archivo
    with open('pos/serializers.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("✅ Campos de delivery agregados a VentaInputSerializer")
else:
    print("❌ No se encontró la línea esperada")
    sys.exit(1)
