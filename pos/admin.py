from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Categoria)
admin.site.register(Nutricional)
admin.site.register(Producto)
admin.site.register(Alerta)
admin.site.register(Cliente)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(MovimientoInventario)
admin.site.register(Empleado)
admin.site.register(Turno)