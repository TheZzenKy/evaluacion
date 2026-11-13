from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "categoría"
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    precio = models.IntegerField()
    stock = models.IntegerField(default=0)
    disponible = models.BooleanField(default=True)
    creado = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "producto"
        verbose_name_plural = "productos"
        constraints = [
            models.CheckConstraint(condition=models.Q(precio__gte=0), name="producto_precio_no_negativo"),
            models.CheckConstraint(condition=models.Q(stock__gte=0), name="producto_stock_no_negativo"),
        ]

    def clean(self):
        errores = {}

        if (
            len(self.codigo) != 7
            or not self.codigo.startswith("CAF-")
            or not self.codigo[4:].isdigit()
        ):
            errores["codigo"] = "El código debe tener el formato CAF-000."
        if self.precio < 100 or self.precio > 20000:
            errores["precio"] = "El precio debe estar entre $100 y $20.000."
        if self.stock < 0:
            errores["stock"] = "El stock no puede ser negativo."

        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return self.nombre


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PREPARANDO = "preparando", "Preparando"
        LISTO = "listo", "Listo"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    cliente = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    hora_retiro = models.TimeField()
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente.username}"


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="detalles",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="detalles_pedido",
    )
    cantidad = models.IntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.IntegerField(validators=[MinValueValidator(0)])
    subtotal = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = "detalle de pedido"
        verbose_name_plural = "detalles de pedido"
        constraints = [
            models.UniqueConstraint(
                fields=["pedido", "producto"],
                name="detalle_producto_unico_por_pedido",
            ),
            models.CheckConstraint(condition=models.Q(cantidad__gte=1), name="detalle_cantidad_positiva"),
            models.CheckConstraint(condition=models.Q(precio_unitario__gte=0), name="detalle_precio_no_negativo"),
            models.CheckConstraint(condition=models.Q(subtotal__gte=0), name="detalle_subtotal_no_negativo"),
        ]

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        Pedido.objects.filter(pk=self.pedido_id).update(
            total=sum(
                detalle.subtotal
                for detalle in self.pedido.detalles.all()
            )
        )
