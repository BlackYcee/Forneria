# Django Core
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.db import transaction, models
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# Python Standard Library
from decimal import Decimal
import requests

# Django REST Framework
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Módulos Locales
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
from .services import procesar_venta
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
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """Devuelve solo las direcciones del cliente asociado al usuario logueado."""
        user = self.request.user
        
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
        cliente = user.empleado.cliente
        serializer.save(cliente=cliente)


def inicio(request):
    """Vista para la página de inicio del POS con productos y categorías."""
    # Intentar obtener datos por ORM
    try:
        categorias_qs = Categoria.objects.all()
        productos_qs = Producto.objects.select_related('categoria').prefetch_related('lotes').all()

        # Filtros
        buscar = request.GET.get("buscar", "").strip()
        categoria_filtro = request.GET.get("categorias", "").strip()

        if buscar:
            productos_qs = productos_qs.filter(models.Q(nombre__icontains=buscar) | models.Q(codigo_barra__startswith=buscar))

        if categoria_filtro:
            productos_qs = productos_qs.filter(categoria__id=categoria_filtro)

        # Convertir a lista de dicts tal como la plantilla espera (campos mínimos)
        productos = []
        for p in productos_qs:
            productos.append({
                'id': p.id,
                'nombre': p.nombre,
                'codigo_barra': p.codigo_barra,
                'precio': float(p.precio_venta) if p.precio_venta is not None else 0,
                'stock_total': p.stock_total(),
                'categoria': p.categoria.id if p.categoria else None,
            })

        categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]

    except Exception:
        # Fallback: usar API HTTP si algo falla con la ORM (evita romper la vista)
        try:
            productos = requests.get("http://127.0.0.1:8000/pos/productos/").json()
            categorias = requests.get("http://127.0.0.1:8000/pos/categorias/").json()
        except Exception:
            productos = []
            categorias = []

    # Paginación
    paginator = Paginator(productos, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, "pos.html", {
        "categorias": categorias,
        "page_obj": page_obj
    })
        
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

        item_existente = ItemCarrito.objects.filter(carrito=carrito, producto_id=producto_id).first()
        
        if item_existente:
            item_existente.cantidad += cantidad
            item_existente.save()
            return Response(ItemCarritoSerializer(item_existente).data, status=status.HTTP_200_OK)
        else:
            serializer.save(carrito=carrito)
            
    @action(detail=False, methods=['delete'])
    def vaciar(self, request):
        """Vacía todos los items del carrito."""
        carrito = self.get_carrito()
        carrito.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Devuelve el resumen del carrito con totales."""
        carrito = self.get_carrito()
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)


@csrf_exempt
@api_view(['POST'])
def checkout(request):
    """Endpoint simple para procesar el checkout.

    Payload esperado (JSON):
    {
      "canal_venta": "presencial",
      "cliente_rut": "12345678-9",          # opcional
      "monto_pagado": 10000,                 # opcional (number)
      "items": [
         {"producto_id": 1, "cantidad": 2, "precio_unitario": 1200, "descuento_pct": 0},
         ...
      ]
    }

    Crea Venta y DetalleVenta dentro de una transacción atómica y consume stock
    usando Venta.actualizar_stock(). Retorna JSON con id/folio/total/vuelto.
    """
    data = request.data
    items = data.get('items') or []
    if not items:
        return Response({'detail': 'No hay items en el carrito'}, status=status.HTTP_400_BAD_REQUEST)

    canal = data.get('canal_venta', 'presencial')
    cliente_rut = data.get('cliente_rut')
    monto_pagado = data.get('monto_pagado')

    try:
        # calcular totales con Decimal
        subtotal = Decimal('0')
        descuento_total = Decimal('0')
        detalles_to_create = []
        for it in items:
            pid = it.get('producto_id')
            qty = int(it.get('cantidad', 0))
            precio = Decimal(str(it.get('precio_unitario', '0')))
            desc_pct = Decimal(str(it.get('descuento_pct') or 0))
            if qty <= 0 or precio <= 0:
                raise ValueError('Cantidad y precio deben ser mayores a 0')
            linea_total = precio * qty
            descuento_linea = (linea_total * desc_pct / Decimal('100')) if desc_pct else Decimal('0')
            subtotal += linea_total
            descuento_total += descuento_linea
            detalles_to_create.append({'producto_id': pid, 'cantidad': qty, 'precio_unitario': precio, 'descuento_pct': desc_pct})

        total_sin_iva = (subtotal - descuento_total).quantize(Decimal('0.01'))
        total_iva = (total_sin_iva * Decimal('0.19')).quantize(Decimal('0.01'))
        total_con_iva = (total_sin_iva + total_iva).quantize(Decimal('0.01'))

        monto_pagado_dec = None
        vuelto = None
        if monto_pagado is not None:
            monto_pagado_dec = Decimal(str(monto_pagado)).quantize(Decimal('0.01'))
            if monto_pagado_dec < total_con_iva:
                return Response({'detail': 'El monto pagado es menor al total'}, status=status.HTTP_400_BAD_REQUEST)
            vuelto = (monto_pagado_dec - total_con_iva).quantize(Decimal('0.01'))

        with transaction.atomic():
            venta = Venta.objects.create(
                fecha=timezone.now(),
                total_sin_iva=total_sin_iva,
                total_iva=total_iva,
                descuento=descuento_total.quantize(Decimal('0.01')),
                total_con_iva=total_con_iva,
                canal_venta=canal,
                monto_pagado=monto_pagado_dec,
                vuelto=vuelto
            )

            # si viene cliente_rut, enlazar cliente
            if cliente_rut:
                from .models import Cliente
                cliente, created = Cliente.objects.get_or_create(rut=cliente_rut, defaults={'nombre': None, 'correo': None})
                venta.cliente = cliente
                venta.save(update_fields=['cliente'])

            # crear detalles
            for d in detalles_to_create:
                prod = Producto.objects.get(id=d['producto_id'])
                DetalleVenta.objects.create(
                    venta=venta,
                    producto=prod,
                    cantidad=d['cantidad'],
                    precio_unitario=d['precio_unitario'],
                    descuento_pct=d['descuento_pct']
                )

            # recalcular y guardar totales por si hay reglas adicionales
            venta.calcular_totales_desde_detalles()

            # consumir stock (puede lanzar ValueError si no hay stock suficiente)
            venta.actualizar_stock()

            # asignar folio simple
            venta.folio = f"V{venta.id:06d}"
            venta.save(update_fields=['folio'])

        resp = {
            'id': venta.id,
            'folio': venta.folio,
            'total_con_iva': str(venta.total_con_iva),
            'vuelto': str(venta.vuelto) if venta.vuelto is not None else None
        }
        return Response(resp, status=status.HTTP_201_CREATED)

    except Producto.DoesNotExist:
        return Response({'detail': 'Producto no encontrado'}, status=status.HTTP_400_BAD_REQUEST)
    except ValueError as ve:
        return Response({'detail': str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'detail': 'Error al procesar la venta', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductosStockBajoList(generics.ListAPIView):
    """
    Retorna una lista de productos cuyo stock físico actual
    es menor o igual a su stock mínimo global.
    """
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """Filtra los productos donde el stock_fisico es <= stock_minimo_global."""
        return Producto.objects.filter(stock_fisico__lte=models.F('stock_minimo_global'))
