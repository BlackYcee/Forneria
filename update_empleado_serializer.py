#!/usr/bin/env python
"""Script para actualizar EmpleadoSerializer para crear usuarios automáticamente"""

filepath = 'pos/serializers.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar EmpleadoSerializer
old_serializer = """class EmpleadoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='__str__', read_only=True)
    
    class Meta:
        model = Empleado
        fields = '__all__'"""

new_serializer = """class EmpleadoSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(required=True)
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = Empleado
        fields = ['id', 'nombres', 'apellido_paterno', 'run', 'correo', 'fono', 
                  'clave', 'direccion', 'cargo', 'nombre_completo', 'username', 'password']
    
    def create(self, validated_data):
        # Extraer campos de usuario
        username = validated_data.pop('username')
        password = validated_data.pop('password')
        nombre_completo = validated_data.pop('nombre_completo', '')
        
        # Separar nombre y apellido si viene en nombre_completo
        partes = nombre_completo.split(' ', 1)
        nombres = partes[0] if partes else 'Sin nombre'
        apellido = partes[1] if len(partes) > 1 else 'Sin apellido'
        
        # Crear el usuario automáticamente
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=nombres,
            last_name=apellido
        )
        
        # Actualizar validated_data con los nombres
        validated_data['nombres'] = nombres
        validated_data['apellido_paterno'] = apellido
        validated_data['usuario'] = user
        
        # Crear el empleado
        empleado = Empleado.objects.create(**validated_data)
        return empleado"""

if old_serializer in content:
    content = content.replace(old_serializer, new_serializer)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ EmpleadoSerializer actualizado exitosamente")
else:
    print("⚠️ No se encontró EmpleadoSerializer original")
