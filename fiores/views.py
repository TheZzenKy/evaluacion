from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .forms import CategoriaForm, PedidoForm, ProductoForm
from .models import Categoria, DetallePedido, Pedido, Producto


def revisar_encargado(request):
    if not request.user.is_staff:
        raise PermissionDenied


@login_required
def inicio(request):
    if request.user.is_staff:
        return redirect("panel_encargado")
    return redirect("panel_cliente")


@login_required
def panel_cliente(request):
    return redirect("catalogo")


@login_required
def catalogo(request):
    productos = Producto.objects.filter(
        disponible=True,
        categoria__activa=True,
    ).select_related("categoria")
    categorias = Categoria.objects.filter(activa=True)
    busqueda = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()

    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    if categoria_id.isdecimal():
        productos = productos.filter(categoria_id=int(categoria_id))

    return render(
        request,
        "fiores/catalogo.html",
        {
            "productos": productos,
            "categorias": categorias,
            "busqueda": busqueda,
            "categoria_id": categoria_id,
        },
    )


@login_required
def carrito(request, pk=None):
    carrito = request.session.get("carrito", {})

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "agregar":
            producto = get_object_or_404(Producto, pk=pk)
            cantidad = int(carrito.get(str(pk), 0))
            if cantidad + 1 > producto.stock:
                messages.error(request, "No hay suficiente stock.")
            elif sum(carrito.values()) + 1 > 10:
                messages.error(request, "No puede agregar más de 10 unidades.")
            else:
                carrito[str(pk)] = cantidad + 1
                request.session["carrito"] = carrito
                request.session.modified = True
            return redirect("catalogo")

        if accion == "actualizar":
            nuevo_carrito = {}
            unidades = 0
            for clave in carrito:
                cantidad = int(request.POST.get("cantidad_" + clave, 0))
                producto = Producto.objects.get(pk=clave)
                if cantidad > producto.stock:
                    messages.error(request, "La cantidad supera el stock.")
                    return redirect("ver_carrito")
                if cantidad > 0:
                    nuevo_carrito[clave] = cantidad
                    unidades += cantidad
            if unidades > 10:
                messages.error(request, "No puede tener más de 10 unidades.")
            else:
                request.session["carrito"] = nuevo_carrito
                request.session.modified = True
            return redirect("ver_carrito")

        if accion == "quitar":
            carrito.pop(str(pk), None)
            request.session["carrito"] = carrito
            request.session.modified = True
            return redirect("ver_carrito")

        if accion == "vaciar":
            request.session["carrito"] = {}
            request.session.modified = True
            return redirect("ver_carrito")

    productos = Producto.objects.filter(pk__in=carrito.keys())
    items = []
    total = 0

    for producto in productos:
        cantidad = int(carrito[str(producto.pk)])
        subtotal = cantidad * producto.precio
        items.append({"producto": producto, "cantidad": cantidad, "subtotal": subtotal})
        total += subtotal

    return render(request, "fiores/carrito.html", {"items": items, "total": total})


@login_required
def confirmar_pedido(request):
    carrito = request.session.get("carrito", {})
    if not carrito:
        messages.error(request, "El carrito está vacío.")
        return redirect("ver_carrito")

    form = PedidoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            productos = Producto.objects.select_for_update().filter(pk__in=carrito.keys())
            total = 0
            unidades = 0
            for producto in productos:
                cantidad = int(carrito[str(producto.pk)])
                if cantidad > producto.stock:
                    messages.error(request, "No hay stock suficiente de " + producto.nombre)
                    return render(request, "fiores/confirmar_pedido.html", {"form": form})
                total += cantidad * producto.precio
                unidades += cantidad

            if unidades > 10:
                messages.error(request, "El pedido no puede tener más de 10 unidades.")
                return render(request, "fiores/confirmar_pedido.html", {"form": form})

            pedido = Pedido.objects.create(
                cliente=request.user,
                hora_retiro=form.cleaned_data["hora_retiro"],
                observaciones=form.cleaned_data["observaciones"],
                total=total,
            )
            for producto in productos:
                cantidad = int(carrito[str(producto.pk)])
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                )
                producto.stock -= cantidad
                producto.save(update_fields=["stock"])

        request.session["carrito"] = {}
        request.session.modified = True
        messages.success(request, "Pedido confirmado correctamente.")
        return redirect("panel_cliente")

    return render(request, "fiores/confirmar_pedido.html", {"form": form})


@login_required
def panel_encargado(request):
    revisar_encargado(request)
    return render(request, "fiores/panel_encargado.html")


@login_required
def categoria_lista(request):
    revisar_encargado(request)
    categorias = Categoria.objects.all().order_by("nombre")
    return render(request, "fiores/categoria_lista.html", {"categorias": categorias})


@login_required
def categoria_detalle(request, pk):
    revisar_encargado(request)
    categoria = get_object_or_404(Categoria, pk=pk)
    return render(request, "fiores/categoria_detalle.html", {"categoria": categoria})


@login_required
def categoria_crear(request):
    revisar_encargado(request)
    form = CategoriaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        categoria = form.save()
        messages.success(request, "Categoría creada correctamente.")
        return redirect("categoria_detalle", pk=categoria.pk)
    return render(request, "fiores/categoria_form.html", {"form": form, "titulo": "Crear categoría"})


@login_required
def categoria_editar(request, pk):
    revisar_encargado(request)
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Categoría actualizada correctamente.")
        return redirect("categoria_detalle", pk=categoria.pk)
    return render(request, "fiores/categoria_form.html", {"form": form, "titulo": "Editar categoría"})


@login_required
def categoria_eliminar(request, pk):
    revisar_encargado(request)
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        try:
            categoria.delete()
        except ProtectedError:
            messages.error(request, "No se puede eliminar una categoría con productos.")
        else:
            messages.success(request, "Categoría eliminada correctamente.")
        return redirect("categoria_lista")
    return render(request, "fiores/confirmar_eliminacion.html", {
        "objeto": categoria,
        "tipo": "categoría",
        "cancelar_url": "categoria_detalle",
    })


@login_required
def producto_lista(request):
    revisar_encargado(request)
    productos = Producto.objects.all().order_by("nombre")
    categorias = Categoria.objects.all()
    busqueda = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    disponible = request.GET.get("disponible", "").strip()

    if busqueda:
        productos = productos.filter(Q(nombre__icontains=busqueda) | Q(codigo__icontains=busqueda))
    if categoria_id.isdecimal():
        productos = productos.filter(categoria_id=int(categoria_id))
    if disponible in ("0", "1"):
        productos = productos.filter(disponible=disponible == "1")

    datos = {
        "productos": productos,
        "categorias": categorias,
        "busqueda": busqueda,
        "categoria_id": categoria_id,
        "disponible": disponible,
    }
    return render(request, "fiores/producto_lista.html", datos)


@login_required
def producto_detalle(request, pk):
    revisar_encargado(request)
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, "fiores/producto_detalle.html", {"producto": producto})


@login_required
def producto_crear(request):
    revisar_encargado(request)
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        producto = form.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("producto_detalle", pk=producto.pk)
    return render(request, "fiores/producto_form.html", {"form": form, "titulo": "Crear producto"})


@login_required
def producto_editar(request, pk):
    revisar_encargado(request)
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=producto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("producto_detalle", pk=producto.pk)
    return render(request, "fiores/producto_form.html", {"form": form, "titulo": "Editar producto"})


@login_required
def producto_eliminar(request, pk):
    revisar_encargado(request)
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        try:
            producto.delete()
        except ProtectedError:
            messages.error(request, "No se puede eliminar un producto que aparece en un pedido.")
        else:
            messages.success(request, "Producto eliminado correctamente.")
        return redirect("producto_lista")
    return render(request, "fiores/confirmar_eliminacion.html", {
        "objeto": producto,
        "tipo": "producto",
        "cancelar_url": "producto_detalle",
    })
