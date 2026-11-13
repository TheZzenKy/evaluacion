from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.test import TestCase

from .admin import PedidoAdmin
from .models import Categoria, DetallePedido, Pedido, Producto


class ModeloDatosTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Café")
        self.producto = Producto.objects.create(
            codigo="CAF001",
            nombre="Espresso",
            precio=1800,
            stock=5,
            categoria=self.categoria,
        )
        self.cliente = User.objects.create(
            username="cliente",
            first_name="Cliente de prueba",
            email="cliente@example.com",
        )

    def test_no_se_puede_eliminar_categoria_con_productos(self):
        with self.assertRaises(ProtectedError):
            self.categoria.delete()

    def test_no_se_puede_eliminar_producto_que_esta_en_un_pedido(self):
        pedido = Pedido.objects.create(cliente=self.cliente, hora_retiro="10:00")
        DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=self.producto.precio,
        )

        with self.assertRaises(ProtectedError):
            self.producto.delete()

    def test_total_del_pedido_y_detalle(self):
        pedido = Pedido.objects.create(cliente=self.cliente, hora_retiro="10:00")
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=self.producto.precio,
        )

        self.assertEqual(detalle.subtotal, 3600)
        pedido.refresh_from_db()
        self.assertEqual(pedido.total, 3600)

    def test_pedido_tiene_detalles_dentro_del_admin(self):
        self.assertIn(Pedido, site._registry)
        pedido_admin = site._registry[Pedido]
        self.assertIsInstance(pedido_admin, PedidoAdmin)
        self.assertEqual(pedido_admin.inlines, PedidoAdmin.inlines)
