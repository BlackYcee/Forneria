from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.nombre or f"Categoría {self.id}"


# Información nutricional
class Nutricional(models.Model):
    calorias = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    proteinas = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    grasas = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    carbohidratos = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    azucares = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sodio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    producto = models.OneToOneField("Producto", on_delete=models.CASCADE, related_name="nutricional", null=True, blank=True)

# Producto
class Producto(models.Model):
    codigo_barra = models.CharField(max_length=50, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=300, null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=100, null=True, blank=True)
    presentacion = models.CharField(max_length=100, null=True, blank=True)
    formato = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    
    def __str__(self):
        return self.nombre

class Lote(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="lotes")
    numero_lote = models.CharField(max_length=50, null=True, blank=True)
    fecha_elaboracion = models.DateField(null=True, blank=True)
    fecha_caducidad = models.DateField()
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(null=True, blank=True)
    stock_maximo = models.IntegerField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)
    eliminado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Lote {self.numero_lote or self.id} - {self.producto.nombre}"

# Alertas sobre productos
class Alerta(models.Model):
    TIPO_ALERTA_CHOICES = [
        ('verde', 'Verde'),
        ('amarilla', 'Amarilla'),
        ('roja', 'Roja'),
    ]
    tipo_alerta = models.CharField(max_length=10, choices=TIPO_ALERTA_CHOICES)
    mensaje = models.CharField(max_length=255)
    fecha_generada = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

# Cliente
class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=150, null=True, blank=True)
    correo = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.nombre

# Empleado
class Empleado(models.Model):
    run = models.CharField(max_length=45, unique=True)
    fono = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=200)
    cargo = models.CharField(max_length=45)

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"

# Venta
class Venta(models.Model):
    CANAL_VENTA_CHOICES = [
        ('presencial', 'Presencial'),
        ('delivery', 'Delivery'),
    ]
    fecha = models.DateTimeField()
    total_sin_iva = models.DecimalField(max_digits=10, decimal_places=2)
    total_iva = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2)
    total_con_iva = models.DecimalField(max_digits=10, decimal_places=2)
    canal_venta = models.CharField(max_length=20, choices=CANAL_VENTA_CHOICES)
    folio = models.CharField(max_length=20, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True)

# Detalle de cada producto vendido
class DetalleVenta(models.Model):
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)


class Pago(models.Model):
    METODO_CHOICES = [
        ('EFE', 'Efectivo'),
        ('DEB', 'Débito'),
        ('CRE', 'Crédito'),
    ]
    
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=3, choices=METODO_CHOICES)
    referencia = models.CharField(max_length=50, null=True, blank=True, help_text="Nro Operación Transbank")
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.monto} ({self.get_metodo_display()})"
    

# Movimiento de inventario
class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)

# Turno de trabajo
class Turno(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='turnos')
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    def __str__(self):
        return f"Turno de {self.empleado} el {self.fecha}"
