from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.test import TestCase, override_settings

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


@override_settings(ROOT_URLCONF="cafeteria.urls")
class AutenticacionRolesTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cliente",
            password="cliente123",
        )
        self.encargado = User.objects.create_user(
            username="encargado",
            password="encargado123",
            is_staff=True,
        )

    def test_usuario_anonimo_debe_iniciar_sesion(self):
        response = self.client.get("/")

        self.assertRedirects(response, "/iniciar-sesion/?next=/")

    def test_cliente_accede_a_su_panel_pero_no_al_panel_de_encargado(self):
        self.client.login(username="cliente", password="cliente123")

        self.assertEqual(self.client.get("/cliente/").status_code, 200)
        self.assertEqual(self.client.get("/encargado/").status_code, 403)

    def test_encargado_accede_a_su_panel_y_el_menu_muestra_el_rol(self):
        self.client.login(username="encargado", password="encargado123")

        response = self.client.get("/encargado/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "encargado")
        self.assertContains(response, "Encargado")

    def test_sesion_expira_en_30_minutos(self):
        self.client.login(username="cliente", password="cliente123")

        self.assertEqual(self.client.session.get_expiry_age(), 1800)

    def test_cerrar_sesion_redirige_al_login(self):
        self.client.login(username="cliente", password="cliente123")

        response = self.client.post("/cerrar-sesion/")

        self.assertRedirects(response, "/iniciar-sesion/")
