from django.shortcuts import render
import requests
from rest_framework import viewsets
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from django.core.paginator import Paginator
from .serializer import *
from .models import *

# Nota: la vista `inicio` intentará usar ORM para obtener productos y categorías
# (más rápido y seguro), y caerá de forma silenciosa al fallback HTTP a la API si
# por alguna razón la consulta ORM falla (por ejemplo, durante despliegues o tests aislados).
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



# TEMPORALMENTE COMENTADO - Modelo Pago no existe
# class PagoViewSet(viewsets.ModelViewSet):
#     queryset = Pago.objects.all()
#     serializer_class = PagoSerializer

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
    
    
def inicio(request):
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
                'precio': float(p.precio) if p.precio is not None else 0,
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

    # Paginación: 8 productos por página
    paginator = Paginator(productos, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "pos.html", {
        "categorias": categorias,
        "page_obj": page_obj
    })


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