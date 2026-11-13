from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto


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
