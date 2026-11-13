from datetime import datetime, timedelta

from django import forms
from django.utils import timezone

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


class PedidoForm(forms.Form):
    hora_retiro = forms.TimeField(
        label="Hora de retiro",
        input_formats=["%H:%M"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea,
    )

    def clean_hora_retiro(self):
        hora = self.cleaned_data["hora_retiro"]
        ahora = timezone.localtime().replace(tzinfo=None)
        retiro = datetime.combine(ahora.date(), hora)

        if hora.hour < 8 or hora.hour > 18:
            raise forms.ValidationError("La hora debe estar entre las 08:00 y 18:00.")
        if retiro < ahora + timedelta(minutes=20):
            raise forms.ValidationError(
                "La hora debe ser al menos 20 minutos después de la hora actual."
            )
        return hora
