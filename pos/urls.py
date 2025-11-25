from django.urls import path,include
from rest_framework import routers
from dj_rest_auth.views import LoginView
from . import views


router=routers.DefaultRouter()
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'nutricionales', views.NutricionalViewSet)
router.register(r'lotes', views.LoteViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'alertas', views.AlertaViewSet)
router.register(r'clientes', views.ClienteViewSet)
router.register(r'ventas', views.VentaViewSet)
# router.register(r'pagos', views.PagoViewSet)  # COMENTADO - Modelo Pago no existe
router.register(r'detalle-ventas', views.DetalleVentaViewSet)
router.register(r'movimientos-inventario', views.MovimientoInventarioViewSet)
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'turnos', views.TurnoViewSet)

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('', include(router.urls)),
    path("sistema/", views.inicio, name='inicio')
]
