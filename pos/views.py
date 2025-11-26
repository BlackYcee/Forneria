from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.exceptions import ValidationError # Importar ValidationError
import requests
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
# Módulos de Terceros
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

# Módulos Locales de la Aplicación
from .serializers import (
    CategoriaSerializer, NutricionalSerializer, LoteSerializer, ProductoSerializer, 
    AlertaSerializer, ClienteSerializer, VentaSerializer, PagoSerializer, 
    DetalleVentaSerializer, MovimientoInventarioSerializer, EmpleadoSerializer, 
    TurnoSerializer, DireccionSerializer, ItemCarritoSerializer, CarritoSerializer
)
from .models import (
    Categoria, Nutricional, Lote, Producto, Alerta, Cliente, Venta, Pago, 
    DetalleVenta, MovimientoInventario, Empleado, Turno, Direccion, Carrito, 
    ItemCarrito
)
from .services import procesar_venta # El servicio para la lógica de negocio

# Create your views here.

#API REST
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class NutricionalViewSet(viewsets.ModelViewSet):
    queryset = Nutricional.objects.all()
    serializer_class = NutricionalSerializer

class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.all()
    serializer_class = LoteSerializer
    
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

class AlertaViewSet(viewsets.ModelViewSet):
    queryset = Alerta.objects.all()
    serializer_class = AlertaSerializer

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer

class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer

class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer

class EmpleadoViewSet(viewsets.ModelViewSet):
    queryset = Empleado.objects.all()
    serializer_class = EmpleadoSerializer

class TurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    



def finalizar_compra_view(request):
    if request.method == 'POST':
        try:
            # 1. Obtener datos del carrito del usuario
            carrito = Carrito.objects.get(session_key=request.session.session_key)
            items = []
            for item in carrito.items.all():
                items.append({'producto_id': item.producto.id, 'cantidad': item.cantidad})
            
            # 2. Datos del formulario de pago
            pago_info = {
                'metodo': request.POST.get('metodo_pago'), # 'DEB', 'CRE', etc
                'monto': 0, # Se calculará o validará adentro
                'referencia': 'TRANSBANK-123' 
            }
            
            # 3. Llamar al servicio MÁGICO
            venta_creada = procesar_venta(
                cliente=carrito.cliente,
                items_data=items,
                metodo_pago_info=pago_info,
                canal='web'
            )
            
            # 4. Limpiar carrito tras éxito
            carrito.delete()
            
            return JsonResponse({'status': 'ok', 'venta_id': venta_creada.id})

        except ValidationError as e:
            return JsonResponse({'status': 'error', 'mensaje': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'mensaje': 'Error interno'}, status=500)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permite acceso de lectura a todos, pero solo el propietario puede editar/eliminar."""
    def has_object_permission(self, request, view, obj):
        # Permite GET, HEAD, OPTIONS (métodos seguros) a cualquiera
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Permite escritura (PUT, PATCH, DELETE) solo si el usuario es el dueño
        # Asumiendo que el User de Django está asociado al Cliente
        if not hasattr(request.user, 'empleado'):
            return False # Solo empleados registrados pueden usar el sistema de cliente
            
        cliente = request.user.empleado.cliente # Asumiendo relación User -> Empleado -> Cliente
        return obj.cliente == cliente

class DireccionViewSet(viewsets.ModelViewSet):
    """
    CRUD para las direcciones de un cliente.
    """
    queryset = Direccion.objects.all() 
    
    serializer_class = DireccionSerializer
    # Permiso: Solo lectura para anónimos, escritura solo para el propietario
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Devuelve solo las direcciones del cliente asociado al usuario logueado."""
        user = self.request.user
        
        # CRÍTICO: Asegura que el usuario sea un Empleado asociado a un Cliente
        if not hasattr(user, 'empleado'):
             raise PermissionDenied("Acceso denegado. No está asociado a un Empleado.")
        
        try:
            cliente = user.empleado.cliente
            return Direccion.objects.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            raise PermissionDenied("El usuario no está asociado a un Cliente válido.")

    def perform_create(self, serializer):
        """Asigna automáticamente el cliente logueado a la nueva dirección."""
        user = self.request.user
        # Obtiene el objeto Cliente asociado al usuario (asumiendo User -> Empleado -> Cliente)
        cliente = user.empleado.cliente
        serializer.save(cliente=cliente)
        
class CarritoViewSet(viewsets.ModelViewSet):
    """
    Gestión de los items dentro del Carrito de Compra (E-commerce).
    Un usuario/sesión solo puede interactuar con su propio carrito.
    """
    queryset = ItemCarrito.objects.all()
    serializer_class = ItemCarritoSerializer
    # Permitimos acceso incluso a no autenticados (usando session_key)
    permission_classes = [permissions.AllowAny] 

    def get_carrito(self):
        """Obtiene o crea el carrito activo para el usuario/sesión."""
        user = self.request.user
        
        if user.is_authenticated:
            # Opción 1: Usuario autenticado (asumiendo User -> Empleado -> Cliente)
            try:
                cliente = user.empleado.cliente
                carrito, created = Carrito.objects.get_or_create(cliente=cliente)
                # Si existe un carrito por sesión, lo migramos al cliente
                if self.request.session.session_key:
                    ses_carrito = Carrito.objects.filter(session_key=self.request.session.session_key).first()
                    if ses_carrito and ses_carrito.id != carrito.id:
                        # Migrar items del carrito temporal al carrito del cliente
                        ItemCarrito.objects.filter(carrito=ses_carrito).update(carrito=carrito)
                        ses_carrito.delete()
                return carrito
            except Exception:
                # Si no está asociado a Cliente, usa la sesión como fallback
                pass
        
        # Opción 2: Usuario anónimo (usando session_key)
        session_key = self.request.session.session_key
        if not session_key:
            self.request.session.save()
            session_key = self.request.session.session_key
            
        carrito, created = Carrito.objects.get_or_create(session_key=session_key, cliente__isnull=True)
        return carrito

    def get_queryset(self):
        """Filtra los items para mostrar solo el contenido del carrito activo."""
        carrito = self.get_carrito()
        return ItemCarrito.objects.filter(carrito=carrito).order_by('id')

    def perform_create(self, serializer):
        """Crea el ItemCarrito, asociándolo al carrito activo."""
        carrito = self.get_carrito()
        producto_id = self.request.data.get('producto')
        cantidad = serializer.validated_data.get('cantidad', 1)

        # Revisa si el producto ya está en el carrito
        item_existente = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        
        if item_existente:
            # Si ya existe, simplemente actualiza la cantidad
            item_existente.cantidad += cantidad
            item_existente.save()
            # Devolver el item actualizado
            return Response(ItemCarritoSerializer(item_existente).data, status=status.HTTP_200_OK)
        else:
            # Si no existe, crea un nuevo item
            serializer.save(carrito=carrito)
            
    # Permite al cliente eliminar todos los items del carrito con un solo llamado
    @action(detail=False, methods=['delete'])
    def vaciar(self, request):
        carrito = self.get_carrito()
        carrito.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Permite al cliente ver el resumen del carrito, incluyendo totales
    @action(detail=False, methods=['get'])
    def resumen(self, request):
        carrito = self.get_carrito()
        serializer = CarritoSerializer(carrito) # Usamos el CarritoSerializer (del modelo padre)
        return Response(serializer.data)
    
    
class VentaCreateAPIView(APIView):
    """
    Endpoint dedicado para procesar una venta completa.
    Utiliza el servicio 'procesar_venta' para asegurar la lógica FIFO
    y la transacción atómica de inventario.
    """
    permission_classes = [permissions.IsAuthenticated] # O permisos adecuados

    def post(self, request, *args, **kwargs):
        # 1. Utiliza un Serializer de entrada (input) para validar los datos
        # Asumiendo que has creado VentaInputSerializer para recibir los datos de la venta.
        serializer = VentaInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # 2. Prepara los datos para el servicio
        items_data = data.pop('items')
        metodo_pago_info = {
            'metodo': data.pop('metodo_pago', None),
            'monto': data.pop('monto_pago', None),
            # Otros campos del modelo Pago
        }
        
        # Asumiendo que la venta se hace a nombre del usuario logueado
        cliente = request.user.empleado.cliente if hasattr(request.user, 'empleado') else None
        empleado = request.user.empleado if hasattr(request.user, 'empleado') else None
        
        # 3. Llama al servicio de negocio FIFO
        try:
            venta_creada = procesar_venta(
                cliente=cliente,
                empleado=empleado,
                items_data=items_data,
                metodo_pago_info=metodo_pago_info,
                canal=data.pop('canal', 'pos'), # O 'web', según el origen
                # Otros parámetros
            )
            
            # 4. Devuelve la respuesta serializada (usando VentaSerializer)
            respuesta_serializer = VentaSerializer(venta_creada)
            return Response(respuesta_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            # Captura errores específicos del servicio (ej. stock insuficiente)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # Captura errores inesperados
            return Response({'error': 'Error interno al procesar la venta: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class ProductosStockBajoList(generics.ListAPIView):
    """
    Retorna una lista de productos cuyo stock físico actual
    es menor o igual a su stock mínimo global.
    """
    serializer_class = ProductoSerializer
    # Solo empleados o usuarios autenticados deben ver reportes
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """
        Filtra los productos donde el stock_fisico es <= stock_minimo_global.
        """
        # CRÍTICO: El campo stock_fisico debe ser el campo cacheado en el modelo Producto
        return Producto.objects.filter(stock_fisico__lte=models.F('stock_minimo_global'))