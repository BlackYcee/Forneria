from django import forms
from .models import Producto, Lote


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'marca', 'precio', 'tipo', 'presentacion', 'formato', 'categoria', 'codigo_barra']


class LoteForm(forms.ModelForm):
    class Meta:
        model = Lote
        fields = ['producto', 'numero_lote', 'fecha_elaboracion', 'fecha_caducidad', 'stock_actual', 'stock_minimo', 'stock_maximo']
