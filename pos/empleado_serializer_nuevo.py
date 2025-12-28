from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Empleado

# Serializer actualizado para crear empleados con usuario automático
class EmpleadoSerializerNuevo(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(required=True, write_only=True)
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
        return empleado
