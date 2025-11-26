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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import csv
from .serializer import *
from .models import *
from .forms import ProductoForm, LoteForm
from django.db.models import Sum, Avg, Count
from django.db.models.functions import TruncDate, TruncMonth


@api_view(['GET'])
def server_time(request):
    """Return current server time in ISO and a human formatted string (es-CL).

    This endpoint is used by the POS frontend to show a server-based timestamp
    when confirming a sale.
    """
    now = timezone.now()
    try:
        formatted = now.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M')
    except Exception:
        formatted = now.strftime('%Y-%m-%d %H:%M')
    return Response({'now': now.isoformat(), 'formatted': formatted})

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


def landing(request):
    """Landing pública: mostrar categorías y productos destacados."""
    try:
        categorias_qs = Categoria.objects.all()
        # permitir filtrar por categoría via GET ?categorias=<id>
        categoria_filtro = request.GET.get('categorias', '').strip()
        productos_qs = Producto.objects.select_related('categoria').prefetch_related('lotes').all()
        if categoria_filtro:
            productos_qs = productos_qs.filter(categoria__id=categoria_filtro)
        productos_qs = productos_qs[:24]

        categorias = [{'id': c.id, 'nombre': c.nombre} for c in categorias_qs]
        productos = []
        for p in productos_qs:
            productos.append({
                'id': p.id,
                'nombre': p.nombre,
                'codigo_barra': p.codigo_barra,
                'precio': float(p.precio) if p.precio is not None else 0,
                'stock_total': p.stock_total(),
                # pasar id y nombre de la categoría para permitir enlaces/filtrado en la plantilla
                'categoria': {'id': p.categoria.id, 'nombre': p.categoria.nombre} if p.categoria else None,
            })
    except Exception:
        # fallback seguro
        categorias = []
        productos = []

    return render(request, 'landing.html', {'categorias': categorias, 'productos': productos, 'categoria_selected': categoria_filtro})


def dashboard(request):
    """Dashboard simple: totales por día y por mes para los últimos 60 días."""
    # Totales por día (últimos 60 días)
    from django.utils import timezone
    hoy = timezone.now()
    fecha_inicio = hoy - timezone.timedelta(days=60)

    ventas_qs = Venta.objects.filter(fecha__gte=fecha_inicio)

    por_dia = (
        ventas_qs
        .annotate(dia=TruncDate('fecha'))
        .values('dia')
        .annotate(total=Sum('total_con_iva'))
        .order_by('dia')
    )

    por_mes = (
        Venta.objects
        .annotate(mes=TruncMonth('fecha'))
        .values('mes')
        .annotate(total=Sum('total_con_iva'))
        .order_by('mes')
    )

    # Convertir QuerySets a listas serializables
    dias = [ { 'dia': r['dia'].isoformat(), 'total': float(r['total'] or 0) } for r in por_dia ]
    meses = [ { 'mes': r['mes'].date().isoformat(), 'total': float(r['total'] or 0) } for r in por_mes ]

    # KPIs simples (últimos 30 días + hoy)
    fecha_30 = hoy - timezone.timedelta(days=30)
    ventas_30_qs = Venta.objects.filter(fecha__gte=fecha_30)

    total_ingresos_30 = ventas_30_qs.aggregate(s=Sum('total_con_iva'))['s'] or 0
    total_ventas_30 = ventas_30_qs.aggregate(c=Count('id'))['c'] or 0
    promedio_venta_30 = ventas_30_qs.aggregate(a=Avg('total_con_iva'))['a'] or 0

    ventas_hoy = Venta.objects.filter(fecha__date=hoy.date()).aggregate(c=Count('id'))['c'] or 0

    kpis = {
        'total_ingresos_30': float(total_ingresos_30),
        'total_ventas_30': int(total_ventas_30),
        'promedio_venta_30': float(promedio_venta_30),
        'ventas_hoy': int(ventas_hoy),
    }

    return render(request, 'pos_dashboard.html', { 'dias': dias, 'meses': meses, 'kpis': kpis })


def ventas_page(request):
    """Página pública interna que lista las ventas recientes."""
    # soportar filtros por cliente (rut o nombre) vía GET
    rut = request.GET.get('rut', '').strip()
    nombre = request.GET.get('nombre', '').strip()

    qs = Venta.objects.select_related('cliente', 'empleado').order_by('-fecha')

    if rut:
        qs = qs.filter(cliente__rut__iexact=rut)
    if nombre:
        qs = qs.filter(cliente__nombre__icontains=nombre)

    # Paginación
    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, 25)  # 25 ventas por página
    page_obj = paginator.get_page(page_number)

    return render(request, 'pos_ventas.html', {'ventas': page_obj.object_list, 'page_obj': page_obj, 'filter_rut': rut, 'filter_nombre': nombre})


def inventario_page(request):
    """Lista simple de productos e información de stock."""
    productos = Producto.objects.select_related('categoria').all()
    # La plantilla de inventario ahora vive en la app `inventario` (inventario/templates/inventario/pos_inventario.html)
    return render(request, 'inventario/pos_inventario.html', {'productos': productos})


def producto_create(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            prod = form.save()
            return render(request, 'inventario/pos_producto_form.html', {'form': form, 'saved': True, 'producto': prod})
    else:
        form = ProductoForm()
    return render(request, 'inventario/pos_producto_form.html', {'form': form})


def producto_edit(request, pk):
    prod = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=prod)
        if form.is_valid():
            prod = form.save()
            return render(request, 'inventario/pos_producto_form.html', {'form': form, 'saved': True, 'producto': prod})
    else:
        form = ProductoForm(instance=prod)
    return render(request, 'inventario/pos_producto_form.html', {'form': form, 'producto': prod})


def producto_delete(request, pk):
    prod = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        prod.delete()
        return render(request, 'inventario/pos_producto_confirm_delete.html', {'deleted': True, 'nombre': prod.nombre})
    return render(request, 'inventario/pos_producto_confirm_delete.html', {'producto': prod})


def product_lotes(request, product_id):
    producto = get_object_or_404(Producto, pk=product_id)
    lotes = producto.lotes.all().order_by('-fecha_elaboracion')
    return render(request, 'inventario/pos_lotes_list.html', {'producto': producto, 'lotes': lotes})


def lote_create(request, product_id=None):
    initial = {}
    producto = None
    if product_id:
        producto = get_object_or_404(Producto, pk=product_id)
        initial['producto'] = producto

    if request.method == 'POST':
        form = LoteForm(request.POST)
        if form.is_valid():
            lote = form.save()
            return render(request, 'inventario/pos_lote_form.html', {'form': form, 'saved': True, 'lote': lote})
    else:
        form = LoteForm(initial=initial)
    return render(request, 'inventario/pos_lote_form.html', {'form': form, 'producto': producto})


def lote_edit(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        form = LoteForm(request.POST, instance=lote)
        if form.is_valid():
            lote = form.save()
            return render(request, 'inventario/pos_lote_form.html', {'form': form, 'saved': True, 'lote': lote})
    else:
        form = LoteForm(instance=lote)
    return render(request, 'inventario/pos_lote_form.html', {'form': form, 'lote': lote})


def lote_delete(request, pk):
    lote = get_object_or_404(Lote, pk=pk)
    if request.method == 'POST':
        nombre = str(lote)
        lote.delete()
        return render(request, 'inventario/pos_lote_confirm_delete.html', {'deleted': True, 'nombre': nombre})
    return render(request, 'inventario/pos_lote_confirm_delete.html', {'lote': lote})


def clientes_page(request):
    clientes = Cliente.objects.all().order_by('nombre')[:200]
    return render(request, 'pos_clientes.html', {'clientes': clientes})


def pedidos_page(request):
    # No hay modelo Pedido en este app; mostrar placeholder y link a ventas
    return render(request, 'pos_pedidos.html', {})


def reportes_page(request):
    # Reusar dashboard como punto de entrada a reportes
    return dashboard(request)


def cliente_detail(request, rut):
    """Detalle de cliente: muestra información y compras paginadas. Soporta export CSV con ?export=csv"""
    cliente = get_object_or_404(Cliente, rut=rut)

    ventas_qs = Venta.objects.filter(cliente=cliente).order_by('-fecha')

    # exportar CSV si se solicita
    if request.GET.get('export') == 'csv':
        # generar CSV de ventas básicas
        response = HttpResponse(content_type='text/csv')
        filename = f"ventas_{cliente.rut}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['folio', 'fecha', 'total_con_iva', 'monto_pagado', 'vuelto', 'canal_venta'])
        for v in ventas_qs:
            writer.writerow([v.folio, v.fecha.isoformat(), str(v.total_con_iva), str(v.monto_pagado or ''), str(v.vuelto or ''), v.canal_venta])
        return response

    # paginación de compras del cliente
    page_number = request.GET.get('page', 1)
    paginator = Paginator(ventas_qs, 20)
    page_obj = paginator.get_page(page_number)

    return render(request, 'pos_cliente_detail.html', {'cliente': cliente, 'ventas': page_obj.object_list, 'page_obj': page_obj})


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
    metodo_pago = data.get('metodo_pago')

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

            # Registrar pago asociado (si se envía método de pago)
            try:
                pago_monto = monto_pagado_dec if monto_pagado_dec is not None else total_con_iva
                if metodo_pago:
                    Pago.objects.create(venta=venta, monto=pago_monto, metodo=metodo_pago)
            except Exception:
                # No bloquear la venta si falla el registro del pago; loguear en futuro
                pass

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