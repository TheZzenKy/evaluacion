from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render


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
    return render(request, "fiores/panel_cliente.html")


@encargado_required
def panel_encargado(request):
    return render(request, "fiores/panel_encargado.html")
