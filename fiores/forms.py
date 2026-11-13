from django import forms

from .models import Categoria, Producto


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre", "descripcion", "activa"]


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            "categoria",
            "codigo",
            "nombre",
            "precio",
            "stock",
            "disponible",
        ]
