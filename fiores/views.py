from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .models import Categoria, Producto


def encargado_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


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


@encargado_required
def panel_encargado(request):
    return render(request, "fiores/panel_encargado.html")
