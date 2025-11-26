from django.db import models
from datetime import date, datetime
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, null=True, blank=True)
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
    codigo_barra = models.IntegerField(null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=300, null=True, blank=True)
    marca = models.CharField(max_length=100, null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=100, null=True, blank=True)
    presentacion = models.CharField(max_length=100, null=True, blank=True)
    formato = models.CharField(max_length=100, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.DO_NOTHING)
    
    def __str__(self):
        return self.nombre

    # Métodos derivables del diagrama
    def stock_total(self):
        """Suma el stock_actual de todos los lotes asociados."""
        return sum(lote.stock_actual or 0 for lote in self.lotes.all())

    def obtener_precio_final(self, con_iva=False, iva_pct=0.19):
        """Precio final opcionalmente incluyendo IVA (por defecto 19%)."""
        precio = float(self.precio or 0)
        if con_iva:
            return round(precio * (1 + float(iva_pct)), 2)
        return round(precio, 2)

    def aplicar_descuento(self, porcentaje, aplicar=False):
        """Calcula precio con descuento; si aplicar=True, actualiza el precio y guarda."""
        if porcentaje is None:
            raise ValueError("Porcentaje requerido")
        if porcentaje < 0 or porcentaje > 100:
            raise ValueError("Porcentaje debe estar entre 0 y 100")
        descuento = float(porcentaje) / 100.0
        nuevo_precio = round(float(self.precio) * (1 - descuento), 2)
        if aplicar:
            self.precio = nuevo_precio
            self.save(update_fields=["precio"])
        return nuevo_precio

    def verificar_disponibilidad_general(self, cantidad):
        """Retorna True si la suma de stock en lotes es suficiente."""
        if cantidad is None or cantidad <= 0:
            return False
        return self.stock_total() >= int(cantidad)

    def registrar_movimiento(self, tipo, cantidad, fecha=None):
        """Crea un movimiento de inventario simple asociado a este producto."""
        from .models import MovimientoInventario
        fecha = fecha or timezone.now()
        mov = MovimientoInventario.objects.create(
            tipo_movimiento=tipo,
            cantidad=int(cantidad),
            fecha=fecha,
            producto=self
        )
        return mov

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

    # Métodos utilitarios según diagrama
    def esta_vencido(self):
        """Retorna True si la fecha de caducidad ya pasó."""
        if not self.fecha_caducidad:
            return False
        return self.fecha_caducidad < date.today()

    def dias_para_caducar(self):
        """Días (enteros) hasta la caducidad. Negativo si ya está vencido."""
        if not self.fecha_caducidad:
            return None
        delta = self.fecha_caducidad - date.today()
        return delta.days

    def agregar_stock(self, cantidad):
        """Agrega stock al lote y lo persiste."""
        if cantidad is None or cantidad <= 0:
            raise ValueError("La cantidad a agregar debe ser mayor a 0")
        self.stock_actual = (self.stock_actual or 0) + int(cantidad)
        self.save(update_fields=["stock_actual", "modificado"])
        return self.stock_actual

    def retirar_stock(self, cantidad):
        """Resta stock del lote si hay suficiente; lanza ValueError si no."""
        if cantidad is None or cantidad <= 0:
            raise ValueError("La cantidad a retirar debe ser mayor a 0")
        if (self.stock_actual or 0) < cantidad:
            raise ValueError("Stock insuficiente en el lote")
        self.stock_actual = int(self.stock_actual) - int(cantidad)
        self.save(update_fields=["stock_actual", "modificado"])
        return self.stock_actual

    def porcentaje_ocupacion(self):
        """Devuelve % de ocupación respecto a stock_maximo, o None si no aplica."""
        if not self.stock_maximo:
            return None
        try:
            return float(self.stock_actual) / float(self.stock_maximo) * 100
        except Exception:
            return None

    def obtener_estado(self):
        """Estado sencillo basado en vencimiento y niveles de stock."""
        if self.esta_vencido():
            return "vencido"
        if self.stock_minimo is not None and self.stock_actual is not None:
            if self.stock_actual < self.stock_minimo:
                return "bajo"
        return "normal"



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
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING)


# Cliente
class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=150, null=True, blank=True)
    correo = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return self.nombre


# Empleado
class Empleado(models.Model):
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=45)
    run = models.CharField(max_length=45, unique=True)
    correo = models.EmailField(max_length=100)
    fono = models.IntegerField(unique=True)
    clave = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    cargo = models.CharField(max_length=45)

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"



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
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vuelto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.DO_NOTHING, null=True, blank=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.DO_NOTHING, null=True, blank=True)

    # Métodos de negocio (resumen básico)
    def detalles(self):
        return self.detalleventa_set.all()

    def calcular_subtotal(self):
        """Suma cantidad * precio_unitario (sin considerar descuentos) de los detalles."""
        return sum((d.cantidad * float(d.precio_unitario)) for d in self.detalles())

    def calcular_total_descuento(self):
        total_desc = 0.0
        for d in self.detalles():
            if d.descuento_pct:
                total_desc += (d.cantidad * float(d.precio_unitario)) * (float(d.descuento_pct) / 100.0)
        return round(total_desc, 2)

    def calcular_totales_desde_detalles(self):
        """Calcula y actualiza los totales de la venta basados en sus detalles."""
        subtotal = self.calcular_subtotal()
        descuento = self.calcular_total_descuento()
        # Asumimos IVA como total_iva ya calculado externamente o usar 19% sobre subtotal-descuento
        iva = round((subtotal - descuento) * 0.19, 2)
        total_sin_iva = round(subtotal - descuento, 2)
        total_con_iva = round(total_sin_iva + iva, 2)
        self.total_sin_iva = total_sin_iva
        self.total_iva = iva
        self.total_con_iva = total_con_iva
        self.save(update_fields=["total_sin_iva", "total_iva", "total_con_iva"])
        return {
            "total_sin_iva": total_sin_iva,
            "total_iva": iva,
            "total_con_iva": total_con_iva,
            "descuento": descuento
        }

    def actualizar_stock(self):
        """Actualiza el stock de los productos restando las cantidades vendidas, consumiendo lotes por fecha de caducidad ascendente."""
        from .models import MovimientoInventario
        for detalle in self.detalles():
            producto = detalle.producto
            cantidad = detalle.cantidad
            # Consumir lotes por fecha de caducidad (próxima a vencer primero)
            lotes = producto.lotes.filter(stock_actual__gt=0).order_by('fecha_caducidad')
            restante = int(cantidad)
            for lote in lotes:
                if restante <= 0:
                    break
                disponible = lote.stock_actual or 0
                to_retirar = min(disponible, restante)
                if to_retirar > 0:
                    lote.retirar_stock(to_retirar)
                    # crear movimiento de salida
                    MovimientoInventario.objects.create(
                        tipo_movimiento='salida',
                        cantidad=to_retirar,
                        fecha=timezone.now(),
                        producto=producto
                    )
                    restante -= to_retirar
            if restante > 0:
                # No alcanzó el stock total; marcar o lanzar excepción según política
                raise ValueError(f"Stock insuficiente para producto {producto.nombre}: falta {restante}")

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
    

# Registro de pagos asociados a una venta
class Pago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo = models.CharField(max_length=50, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.id} - {self.monto}"


# Movimiento de inventario
class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]
    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
    producto = models.ForeignKey(Producto, on_delete=models.DO_NOTHING)

# Turno de trabajo
class Turno(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='turnos')
    fecha = models.DateField()
    hora_entrada = models.TimeField()
    hora_salida = models.TimeField()

    def __str__(self):
        return f"Turno de {self.empleado} el {self.fecha}"
