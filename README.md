# Fiores

Proyecto de una cafetería realizado con Django.

## Instalación

1. Crear y activar un entorno virtual.
2. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

3. Crear la base de datos:

```bash
python manage.py migrate
```

4. Cargar los datos de prueba:

```bash
python manage.py loaddata datos_prueba
```

5. Ejecutar el proyecto:

```bash
python manage.py runserver
```

## Usuarios de prueba

El fixture incluye:

- Encargado: `encargado` / `1234`
- Cliente: `ana` / `1234`
- Cliente: `juan` / `1234`

Para crear un usuario administrador se puede ejecutar:

```bash
python manage.py createsuperuser
```

## Funcionalidades

- Inicio de sesión y roles.
- Catálogo de productos.
- Carrito y confirmación de pedidos.
- Gestión del catálogo para encargados.
- Seguimiento de pedidos.
