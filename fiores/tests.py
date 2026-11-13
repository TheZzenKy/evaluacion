from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.db.models import ProtectedError
from django.test import TestCase, override_settings

from .admin import PedidoAdmin
from .forms import ProductoForm
from .models import Categoria, DetallePedido, Pedido, Producto


class ModeloDatosTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Café")
        self.producto = Producto.objects.create(
            codigo="CAF-001",
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

        self.assertRedirects(self.client.get("/cliente/"), "/cliente/catalogo/")
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


class CatalogoTests(TestCase):
    def setUp(self):
        self.cliente = User.objects.create_user(
            username="cliente_catalogo",
            password="cliente123",
        )
        self.categoria = Categoria.objects.create(nombre="Cafés", activa=True)
        self.otra_categoria = Categoria.objects.create(
            nombre="Inactiva",
            activa=False,
        )
        Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-001",
            nombre="Café Grande",
            precio=1500,
            stock=3,
            disponible=True,
        )
        Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-002",
            nombre="Café Agotado",
            precio=2500,
            stock=0,
            disponible=True,
        )
        Producto.objects.create(
            categoria=self.otra_categoria,
            codigo="CAF-003",
            nombre="Producto Oculto",
            precio=1000,
            stock=2,
            disponible=True,
        )
        Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-004",
            nombre="Producto No Disponible",
            precio=1000,
            stock=2,
            disponible=False,
        )
        self.client.login(username="cliente_catalogo", password="cliente123")

    def test_catalogo_solo_muestra_productos_disponibles_y_categorias_activas(self):
        response = self.client.get("/cliente/catalogo/")

        self.assertContains(response, "Café Grande")
        self.assertContains(response, "Café Agotado")
        self.assertNotContains(response, "Producto Oculto")
        self.assertNotContains(response, "Producto No Disponible")

    def test_catalogo_filtra_por_nombre_y_categoria(self):
        response = self.client.get(
            "/cliente/catalogo/?q=Grande&categoria="
            f"{self.categoria.pk}"
        )

        self.assertContains(response, "Café Grande")
        self.assertNotContains(response, "Café Agotado")

    def test_catalogo_formatea_precios_y_marca_agotados(self):
        response = self.client.get("/cliente/catalogo/")
        contenido = response.content.decode()

        self.assertContains(response, "$1.500")
        self.assertContains(response, "Agotado")
        self.assertIn(
            '<button type="button" disabled>Agregar al carrito</button>',
            contenido,
        )


class GestionCatalogoTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="encargado", password="1234", is_staff=True
        )
        self.categoria = Categoria.objects.create(nombre="Cafes")
        self.producto = Producto.objects.create(
            categoria=self.categoria,
            codigo="CAF-001",
            nombre="Espresso",
            precio=1800,
            stock=5,
        )

    def test_formulario_producto(self):
        form = ProductoForm({
            "categoria": self.categoria.pk,
            "codigo": "ABC",
            "nombre": "Producto",
            "precio": 50,
            "stock": -1,
        })

        self.assertFalse(form.is_valid())
        self.assertTrue("codigo" in form.errors)
        self.assertTrue("precio" in form.errors)
        self.assertTrue("stock" in form.errors)

    def test_crear_producto(self):
        self.client.login(username="encargado", password="1234")

        response = self.client.post("/encargado/productos/crear/", {
            "categoria": self.categoria.pk,
            "codigo": "CAF-002",
            "nombre": "Latte",
            "precio": 2500,
            "stock": 4,
            "disponible": "on",
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Producto.objects.count(), 2)

    def test_filtrar_productos(self):
        otra_categoria = Categoria.objects.create(nombre="Tes")
        Producto.objects.create(
            categoria=otra_categoria,
            codigo="TEA-001",
            nombre="Té negro",
            precio=1500,
            stock=3,
            disponible=False,
        )
        self.client.login(username="encargado", password="1234")
        response = self.client.get("/encargado/productos/?q=TEA")

        self.assertContains(response, "Té negro")
        self.assertNotContains(response, "Espresso")

    def test_no_elimina_categoria_con_productos(self):
        self.client.login(username="encargado", password="1234")

        url = "/encargado/categorias/" + str(self.categoria.id) + "/eliminar/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, follow=True)

        self.assertContains(response, "No se puede eliminar una categoría con productos.")
