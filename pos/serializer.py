from rest_framework import serializers
from .models import * 
from datetime import date, datetime
import re

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
            

class NutricionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nutricional
        fields = '__all__'
    def validate_calorias(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las calorias no pueden ser 0")
        return value
    def validate_proteinas(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las proteinas no pueden ser 0")
        return value
    def validate_grasas(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las grasas no pueden ser 0")
        return value
    def validate_carbohidratos(self, value):
        if value is not None and value< 0:
            raise serializers.ValidationError("Las hidratos de carbono no pueden ser 0")
        return value
    def validate_azucares(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las azúcares no pueden ser 0")
        return value
    def validate_sodio(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Las sodio no pueden ser 0")
        return value

class ProductoSerializer(serializers.ModelSerializer):
    nutricional = NutricionalSerializer(read_only=True)
    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'marca', 'precio',
            'caducidad', 'elaboracion', 'tipo',
            'stock_actual', 'stock_minimo', 'stock_maximo',
            'presentacion', 'formato',
            'creado', 'modificado', 'eliminado',
            'categoria', 'nutricional'
        ]
         # Validación de precio
    def validate_precio(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0.")
        return value

    # Validación de stock_actual
    def validate_stock_actual(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El stock actual no puede ser negativo.")
        return value

    # Validación de stock_minimo
    def validate_stock_minimo(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El stock mínimo no puede ser negativo.")
        return value

    # Validación de stock_maximo
    def validate_stock_maximo(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("El stock máximo no puede ser negativo.")
        return value

    # Validaciones cruzadas
    def validate(self, data):
        # Caducidad debe ser posterior a la fecha de elaboración
        if data.get("elaboracion") and data.get("caducidad"):
            if data["caducidad"] <= data["elaboracion"]:
                raise serializers.ValidationError({
                    "caducidad": "La fecha de caducidad debe ser posterior a la fecha de elaboración."
                })

        # Stock actual debe estar entre mínimo y máximo
        if data.get("stock_minimo") and data.get("stock_maximo") and data.get("stock_actual") is not None:
            if data["stock_minimo"] > data["stock_maximo"]:
                raise serializers.ValidationError({
                    "stock_minimo": "El stock mínimo no puede ser mayor que el stock máximo."
                })
            if not (data["stock_minimo"] <= data["stock_actual"] <= data["stock_maximo"]):
                raise serializers.ValidationError({
                    "stock_actual": "El stock actual debe estar entre el mínimo y el máximo definidos."
                })

        # Caducidad no puede ser en el pasado
        if data.get("caducidad") and data["caducidad"] < date.today():
            raise serializers.ValidationError({
                "caducidad": "La fecha de caducidad no puede estar en el pasado."
            })

        return data

class AlertaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerta
        fields = '__all__'

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'
    
    def validate_rut(self, value):
        if not value:
            raise serializers.ValidationError("El RUT es obligatorio.")

        # Validar formato: 7 u 8 dígitos + guion + dígito verificador (número o K)
        patron = r'^\d{7,8}-[\dkK]$'
        if not re.match(patron, value):
            raise serializers.ValidationError("El RUT debe tener el formato 12345678-5")

        return value

        
    
class VentaSerializer(serializers.ModelSerializer):
    cliente_rut = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Venta
        fields = [
            'id', 'fecha', 'total_sin_iva', 'total_iva', 'descuento',
            'total_con_iva', 'canal_venta', 'folio',
            'monto_pagado', 'vuelto', 'cliente', 'cliente_rut'
        ]
        read_only_fields = ['cliente']
        
    def create(self, validated_data):
        rut = validated_data.pop('cliente_rut', None)
        if rut:
            cliente, created = Cliente.objects.get_or_create(
                rut=rut,
                defaults={
                    "nombre": None,
                    "correo": None
                }
            )
            validated_data['cliente'] = cliente
        return super().create(validated_data)
        
    def validate(self, data):
        # total_con_iva = total_sin_iva + total_iva - descuento
        esperado = data["total_sin_iva"] + data["total_iva"] - data["descuento"]
        if data["total_con_iva"] != esperado:
            raise serializers.ValidationError({
                "total_con_iva": "El total con IVA no coincide con el cálculo esperado."
            })

        # Validación: fecha no puede ser futura
        if data.get("fecha") and data["fecha"].date() > date.today():
            raise serializers.ValidationError({
                "fecha": "La fecha de la venta no puede estar en el futuro."
            })

        # Validación: monto pagado debe ser >= total_con_iva
        if data.get("monto_pagado") is not None:
            if data["monto_pagado"] < data["total_con_iva"]:
                raise serializers.ValidationError({
                    "monto_pagado": "El monto pagado no puede ser menor al total con IVA."
                })

        # Validación: vuelto debe ser correcto
        if data.get("monto_pagado") is not None and data.get("vuelto") is not None:
            esperado_vuelto = data["monto_pagado"] - data["total_con_iva"]
            if data["vuelto"] != esperado_vuelto:
                raise serializers.ValidationError({
                    "vuelto": "El vuelto no coincide con el cálculo esperado."
                })

        return data
    
class DetalleVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleVenta
        fields = '__all__'
        
    def validate_cantidad(self, value):
        if value <= 0:
            raise serializers.ValidationError("La cantidad debe ser mayor a 0.")
        return value

    def validate_precio_unitario(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio unitario debe ser mayor a 0.")
        return value

    def validate_descuento_pct(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError("El descuento debe estar entre 0 y 100%.")
        return value

    def validate(self, data):
        # Validación cruzada: precio con descuento no puede ser negativo
        if data.get("descuento_pct") is not None:
            precio_final = data["precio_unitario"] * (1 - data["descuento_pct"] / 100)
            if precio_final < 0:
                raise serializers.ValidationError({
                    "precio_unitario": "El precio final no puede ser negativo."
                })
        return data

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoInventario
        fields = '__all__'
    def validate(self, data):
        # Validar que la fecha no sea futura
        if data.get("fecha") and data["fecha"] > datetime.now():
            raise serializers.ValidationError({
                "fecha": "La fecha del movimiento no puede estar en el futuro."
            })

        # Validar coherencia de tipo de movimiento
        if data["tipo_movimiento"] == "salida":
            # Validar contra stock actual del producto
            if data["cantidad"] > data["producto"].stock_actual:
                raise serializers.ValidationError({
                    "cantidad": "No puedes retirar más cantidad que el stock disponible."
                })

        return data

class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = '__all__'
        
    def validate_run(self, value):
        if not value:
            raise serializers.ValidationError("El RUN es obligatorio.")
        # Aquí podrías agregar validación de formato RUN chileno
        return value

    def validate_fono(self, value):
        if value <= 0:
            raise serializers.ValidationError("El número de teléfono debe ser positivo.")
        return value

    def validate_correo(self, value):
        if not value or "@" not in value:
            raise serializers.ValidationError("Debe ingresar un correo válido.")
        return value
    
class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields =  '__all__'