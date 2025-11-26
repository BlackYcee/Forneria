from django.urls import path, include
from rest_framework.routers import DefaultRouter
from dj_rest_auth.views import LoginView, LogoutView
from . import views

router = DefaultRouter()

# Catálogo e Inventario
router.register(r'categorias', views.CategoriaViewSet)
router.register(r'nutricionales', views.NutricionalViewSet)
router.register(r'lotes', views.LoteViewSet)
router.register(r'productos', views.ProductoViewSet)
router.register(r'alertas', views.AlertaViewSet)

# Actores y Logística
router.register(r'clientes', views.ClienteViewSet)
router.register(r'direcciones', views.DireccionViewSet) # para gestionar direcciones del cliente
router.register(r'empleados', views.EmpleadoViewSet)
router.register(r'turnos', views.TurnoViewSet)

# E-commerce y Ventas
router.register(r'carrito', views.CarritoViewSet) # para la gestión del carrito
router.register(r'ventas', views.VentaViewSet)
router.register(r'pagos', views.PagoViewSet)
router.register(r'detalle-ventas', views.DetalleVentaViewSet)

# Trazabilidad
router.register(r'movimientos-inventario', views.MovimientoInventarioViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Rutas de autenticación (dj-rest-auth)
    path('auth/login/', LoginView.as_view(), name='rest_login'),
    path('auth/logout/', LogoutView.as_view(), name='rest_logout'),
    
    path('vender/', views.VentaCreateAPIView.as_view(), name='venta-crear-segura'),

    # Rutas para reportes 
    path('reportes/stock-bajo/', views.ProductosStockBajoList.as_view(), name='reporte-stock-bajo'),
]

urlpatterns = [
    path('api/', include(router.urls)),
]
