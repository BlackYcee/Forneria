from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from decimal import Decimal
from django.contrib.auth.models import User 
from .models import (
    Categoria, Producto, Nutricional, Lote, MovimientoInventario, 
    Alerta, Cliente, Direccion, Empleado, Turno, Carrito, ItemCarrito, Venta, 
    DetalleVenta, Pago
)
from inventario.models import Proveedor, Insumo, OrdenCompra, OrdenCompraItem, Ubicacion
from dj_rest_auth.serializers import JWTSerializer
# ==========================================
# 1. INPUT SERIALIZERS 
# ==========================================

class ItemVentaInputSerializer(serializers.Serializer):
    """Para validar la lista de productos y cantidades al crear una venta."""
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)
    # El frontend envía este campo; se acepta pero el precio oficial se toma del producto en servidor
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

class PagoInputSerializer(serializers.Serializer):
    """Para validar la información de pago al crear una venta."""
    metodo = serializers.CharField(max_length=3)
    monto = serializers.DecimalField(max_digits=12, decimal_places=2)
    referencia = serializers.CharField(max_length=100, required=False, allow_null=True)
    
   
    monto_recibido = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
     
class VentaInputSerializer(serializers.Serializer):
    """
    Serializer principal para recibir todos los datos de entrada al procesar una Venta.
    """
    items = ItemVentaInputSerializer(many=True)
    pagos = PagoInputSerializer(many=True)
    cliente_id = serializers.IntegerField(required=False, allow_null=True)
    direccion_id = serializers.IntegerField(required=False, allow_null=True)
    canal = serializers.CharField(max_length=10, required=False)
    # Campos adicionales para Delivery
    direccion_entrega = serializers.CharField(max_length=255, required=False, allow_blank=True)
    referencias = serializers.CharField(max_length=255, required=False, allow_blank=True)
    instrucciones = serializers.CharField(max_length=500, required=False, allow_blank=True)
    cliente_nombre = serializers.CharField(max_length=150, required=False, allow_blank=True)
    cliente_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    cliente_email = serializers.EmailField(required=False, allow_blank=True)

