from django.shortcuts import render
import requests
from rest_framework import viewsets
from django.core.paginator import Paginator
from .serializer import *
from .models import *
# Create your views here.

#API REST
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer

class NutricionalViewSet(viewsets.ModelViewSet):
    queryset = Nutricional.objects.all()
    serializer_class = NutricionalSerializer

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
    
    
#vistas de la app de POS
def inicio(request):
    # Traer productos y categorías desde tu API
    productos = requests.get("http://127.0.0.1:8000/pos/productos/").json()
    categorias = requests.get("http://127.0.0.1:8000/pos/categorias/").json()

    # Filtros
    buscar = request.GET.get("buscar", "").strip()
    categoria_filtro = request.GET.get("categorias", "").strip()

    if buscar:
        productos = [
            p for p in productos
            if buscar.lower() in p["nombre"].lower()
            or str(p.get("codigo_barra", "")).startswith(buscar)
        ]

    if categoria_filtro:
        productos = [
            p for p in productos
            if str(p["categoria"]) == categoria_filtro
        ]

    # Paginación: 8 productos por página
    paginator = Paginator(productos, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "pos.html", {
        "categorias": categorias,
        "page_obj": page_obj
    })