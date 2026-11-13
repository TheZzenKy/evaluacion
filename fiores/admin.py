from django.contrib import admin

from .models import Categoria, DetallePedido, Pedido, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa", "cantidad_productos")
    list_filter = ("activa",)
    search_fields = ("nombre", "descripcion")

    @admin.display(description="Productos")
    def cantidad_productos(self, obj):
        return obj.productos.count()


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo",
        "categoria",
        "precio",
        "stock",
        "disponible",
    )
    list_filter = ("categoria", "disponible")
    search_fields = ("codigo", "nombre")
    list_select_related = ("categoria",)

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1
    autocomplete_fields = ("producto",)
    readonly_fields = ("subtotal",)
    fields = ("producto", "cantidad", "precio_unitario", "subtotal")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "hora_retiro", "estado", "total")
    list_filter = ("estado", "fecha")
    search_fields = ("cliente__username", "cliente__first_name", "cliente__email")
    list_select_related = ("cliente",)
    inlines = (DetallePedidoInline,)

    @admin.display(description="Total")
    def total(self, obj):
        return obj.total


@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "cantidad", "precio_unitario", "subtotal")
    list_filter = ("producto__categoria",)
    search_fields = ("pedido__cliente__username", "producto__nombre", "producto__codigo")
    list_select_related = ("pedido", "producto")

    @admin.display(description="Subtotal")
    def subtotal(self, obj):
        return obj.subtotal
