def carrito(request):
    unidades = 0
    carrito = request.session.get("carrito", {})

    for cantidad in carrito.values():
        unidades += int(cantidad)

    return {"carrito_unidades": unidades}
