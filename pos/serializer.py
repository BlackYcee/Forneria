from rest_framework import serializers
from .models import * 

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class NutricionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nutricional
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class VentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venta
        fields = '__all__'

class DetalleVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVenta
        fields = '__all__'

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoInventario
        fields = '__all__'

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'

class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields =  '__all__'