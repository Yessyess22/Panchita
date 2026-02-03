# Revisión completa del proyecto Panchita

Sistema de punto de venta (POS) y gestión para **Pollos Panchita**, desarrollado en Django. Este documento describe **carpeta por carpeta** y **archivo por archivo** qué se ejecuta y para qué sirve.

---

## Estructura general

```
Panchita/
├── PanchitaApp/          ← Proyecto Django (raíz de la aplicación)
│   ├── gestion/         ← App principal (modelos, vistas, URLs, plantillas)
│   ├── panchita_project/← Configuración del proyecto (settings, URLs raíz, WSGI)
│   ├── media/           ← Archivos subidos (imágenes de productos)
│   ├── manage.py        ← Punto de entrada para comandos Django
│   ├── requirements.txt ← Dependencias Python
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── start.sh / start.bat
│   └── ...
```

---

## 1. Raíz del repositorio: `Panchita/`

- **`.DS_Store`**: Archivo de sistema macOS (ignorado en Git).
- **`PanchitaApp/`**: Contiene todo el proyecto Django. Es la carpeta donde se ejecuta `manage.py`, Docker y scripts de arranque.

---

## 2. Raíz del proyecto Django: `PanchitaApp/`

### 2.1 `manage.py`

**Qué hace:** Punto de entrada de Django. Define `DJANGO_SETTINGS_MODULE` como `panchita_project.settings` y delega en la línea de comandos de Django.

**Uso:**  
`python manage.py runserver`, `python manage.py migrate`, `python manage.py backup_db`, etc.

---

### 2.2 `requirements.txt`

**Qué hace:** Lista de dependencias Python.

| Paquete       | Uso |
|---------------|-----|
| Django>=4.2,<5| Framework web |
| PyMySQL       | Conexión a MySQL |
| Pillow        | Procesamiento de imágenes (productos) |
| cryptography  | Utilidades criptográficas |

---

### 2.3 `init_data.py`

**Qué hace:** Script para **inicializar datos básicos** (no es una vista ni un comando `manage.py`). Crea categorías (Pollos, Bebidas, Extras), productos de ejemplo (Chiquitin, Chipollo, Escolar, Panchita), métodos de pago (Efectivo, Tarjeta, etc.) y opcionalmente cliente “Mostrador” y usuarios admin/vendedor.

**Ejecución:**  
`Get-Content init_data.py | python manage.py shell` (o cargar en `python manage.py shell`).

---

### 2.4 `load_products.py`

**Qué hace:** Script que **carga productos desde imágenes** en `media/productos/`. Crea o actualiza categorías (Pollos, Bebidas, Extras, Mexicana, Platos, Comida Rápida) y productos asociando imagen, nombre, precio y categoría. Pensado para desarrollo o carga inicial.

**Ejecución:**  
`python load_products.py` (con Django configurado).

---

### 2.5 `docker-compose.yml`

**Qué hace:** Orquesta dos servicios:

- **`web`**: Contenedor Django. Ejecuta migraciones, `collectstatic`, y `runserver 0.0.0.0:8000`. Variables de entorno para DB (host `db`, usuario, contraseña, etc.). Volúmenes para código, `staticfiles` y `media`.
- **`db`**: MySQL 8.0. Base de datos `panchita_db`, usuario `panchita_user`. Puerto expuesto `3309:3306`. Healthcheck para que `web` espere a que MySQL esté listo.

Red `panchita_network` (192.168.100.0/24) y volúmenes para persistir MySQL, estáticos y media.

---

### 2.6 `Dockerfile`

**Qué hace:** Imagen para el servicio `web`. Base `python:3.11-slim`, instala dependencias del sistema para MySQL (`default-libmysqlclient-dev`, etc.), copia `requirements.txt`, instala dependencias Python y copia el proyecto en `/app`.

---

### 2.7 `start.sh`

**Qué hace:** Script **universal de arranque** en Linux/macOS/Git Bash/WSL:

1. **Si hay Docker:** Ofrece usar Docker (reconstruir, inicio rápido, detached, detener, estado). No requiere Python local.
2. **Si no hay Docker:** Modo local con SQLite. Busca Python/venv (`.venv`, `.venv_mac`, `.venv/Scripts` en Windows), instala dependencias si falta Django, crea `media`, `backups`, `staticfiles`, define `DJANGO_USE_SQLITE=1`, ejecuta migraciones y `collectstatic`, opcionalmente carga datos con `load_products.py` e `init_data.py`, y arranca `runserver`.

---

### 2.8 `start.bat`

**Qué hace:** Misma lógica que `start.sh` pero para **Windows** (CMD). Detecta Docker; si no está, usa Python local, venv si existe, SQLite, migraciones y `runserver`.

---

### 2.9 `.gitignore`

**Qué hace:** Excluye del repositorio: entornos virtuales, `__pycache__`, `db.sqlite3`, `backups/`, `staticfiles/`, `.env`, datos de Docker, IDE, logs, etc., para no subir código generado ni secretos.

---

### 2.10 `.dockerignore`

**Qué hace:** Evita copiar al contexto de build de Docker: `mysql_data/`, `__pycache__`, `.git`, `.env`, `venv/`, `.idea`, `.vscode`. Acelera el build y reduce tamaño de imagen.

---

### 2.11 `media/`

**Qué hace:** Raíz de **archivos subidos**. `media/productos/` guarda las imágenes de los productos (PNG, JPG). Django sirve estos archivos en desarrollo vía `MEDIA_URL`/`MEDIA_ROOT` configurados en `settings.py`.

---

### 2.12 Documentación (README, INSTRUCCIONES_DOCKER, etc.)

- **README.md**, **INICIO_RAPIDO.md**, **INFORME_PROYECTO.md**, **INSTRUCCIONES_DOCKER.md**: Instrucciones de uso, Docker e informe del proyecto.
- **DIAGRAMA_BD.png**: Diagrama de base de datos.

---

## 3. Configuración del proyecto: `panchita_project/`

### 3.1 `__init__.py`

**Qué hace:** Marca el directorio como paquete Python. Vacío o con imports si se usan.

---

### 3.2 `settings.py`

**Qué hace:** Configuración central de Django.

- **BASE_DIR**: Raíz del proyecto (`PanchitaApp`).
- **SECRET_KEY**: Por defecto desde `DJANGO_SECRET_KEY`; en producción debe definirse.
- **DEBUG**: Por defecto `True`; en producción `DEBUG=False`.
- **ALLOWED_HOSTS**: Desde `ALLOWED_HOSTS` (CSV) o `*` en desarrollo.
- **INSTALLED_APPS**: `django.contrib.*` y `gestion`.
- **MIDDLEWARE**: Seguridad, sesiones, CSRF, auth, mensajes, etc.
- **ROOT_URLCONF**: `panchita_project.urls`.
- **TEMPLATES**: Motor Django, `APP_DIRS=True` (plantillas en cada app).
- **WSGI_APPLICATION**: `panchita_project.wsgi.application`.
- **Base de datos:**  
  - Si `DJANGO_USE_SQLITE=1`: SQLite (`db.sqlite3`).  
  - Si no: MySQL (host, puerto, nombre, usuario, contraseña desde variables de entorno).
- **AUTH_PASSWORD_VALIDATORS**: Reglas de contraseñas.
- **LANGUAGE_CODE**: `es-bo`, **TIME_ZONE**: `America/La_Paz`.
- **STATIC_URL**, **STATIC_ROOT**, **MEDIA_URL**, **MEDIA_ROOT**: Rutas de estáticos y media.
- **LOGIN_URL**: `'login'`.
- **EMPRESA_NIT**: Opcional, para facturas (comentado).

---

### 3.3 `settings_sqlite.py`

**Qué hace:** Hereda de `settings.py` y **sobrescribe** `DATABASES` para usar solo SQLite. Útil para pruebas o cuando no hay MySQL (también se puede usar `DJANGO_USE_SQLITE=1` con `settings` normal).

---

### 3.4 `urls.py`

**Qué hace:** URLs raíz del proyecto.

- `admin/` → Django Admin.
- `''` → Incluye todas las URLs de la app `gestion` (`gestion.urls`).

En modo DEBUG, añade la ruta para servir archivos de `MEDIA_ROOT` bajo `MEDIA_URL`.

---

### 3.5 `wsgi.py`

**Qué hace:** Punto de entrada **WSGI** para desplegar con servidores como Gunicorn/uWSGI. Define `DJANGO_SETTINGS_MODULE` y devuelve la aplicación Django (`get_wsgi_application()`).

---

## 4. App principal: `gestion/`

Contiene modelos, vistas, URLs, plantillas, estáticos y lógica de negocio del POS y la gestión.

---

### 4.1 `gestion/__init__.py`

**Qué hace:** Convierte `gestion` en paquete Python. Vacío o con configuración de app si se usa.

---

### 4.2 `gestion/apps.py`

**Qué hace:** Define `GestionConfig` (AppConfig) con `name = 'gestion'` y `default_auto_field`. Django lo usa para cargar la app.

---

### 4.3 `gestion/models.py`

**Qué hace:** Define los **modelos de base de datos** (tablas).

| Modelo | Descripción |
|--------|-------------|
| **Categoria** | Nombre, descripción, activo. Agrupa productos. |
| **Producto** | Nombre, descripción, costo, precio_venta, descuento %, stock, categoria, imagen, activo. Métodos: `precio_final()`, `margen_ganancia()`, `tiene_stock()`. |
| **Cliente** | nombre_completo, ci_nit, telefono, email, direccion, activo. Para ventas y facturación. |
| **MetodoPago** | nombre, tipo (efectivo/tarjeta/qr/transferencia), requiere_validacion, activo. |
| **Promocion** | nombre, descripcion, descuento_porcentaje, fecha_inicio/fin, activo, M2M con Producto. Métodos: `esta_vigente()`, `aplicar_a_producto()`. |
| **Venta** | cliente, usuario (vendedor), fecha, tipo_documento (ticket/factura), numero_factura, modo_consumo (local/llevar), subtotal, descuento_total, total, estado (pendiente/completado/cancelado), notas. Métodos: `calcular_totales()`, `tiene_pago_completo()`. |
| **DetalleVenta** | venta, producto, cantidad, precio_unitario, descuento_porcentaje, descuento_aplicado, subtotal. En `save()` calcula descuento y subtotal. |
| **Pago** | venta, metodo_pago, monto, referencia, validado, validado_por, notas. Método `validar_pago(usuario)` y validación en `clean()`. |
| **CierreCaja** | usuario, fecha_cierre, total_ventas, fondo_inicial, fondo_final, notas. |
| **CierreCajaDetallePago** | cierre, metodo_pago, monto. Desglose por método de pago en el cierre. |

---

### 4.4 `gestion/admin.py`

**Qué hace:** Registra los modelos en el **Django Admin** (`/admin/`): Categoria, Producto, Cliente, MetodoPago, Promocion, Venta (con inlines DetalleVenta y Pago), CierreCaja (con inline CierreCajaDetallePago), Pago. Define list_display, list_filter, search_fields, inlines y en Pago un `save_model` que asigna `validado_por` al validar.

---

### 4.5 `gestion/decorators.py`

**Qué hace:** Define el decorador **`@staff_required`**. Comprueba que el usuario esté autenticado y que `user.is_staff` sea True; si no, redirige al `index` con mensaje de acceso denegado. Se usa junto con `@login_required` en vistas de administración (productos, categorías, métodos de pago, promociones, usuarios, reportes).

---

### 4.6 `gestion/urls.py`

**Qué hace:** Define todas las **URLs** de la aplicación (rutas que no son `/admin/`).

- **Auth:** `login/`, `logout/`.
- **Cuenta/Admin:** `cuenta/`, `cuenta/cambiar-password/`, `cuenta/cambiar-password-vendedor/`, `cuenta/usuarios/`, crear, eliminar.
- **Públicas (tras login):** `''` (index), `pos/`, `pos/procesar-pago/`, `pos/buscar-clientes/`, `pos/crear-cliente/`.
- **Productos:** listado, crear, editar, eliminar.
- **Categorías:** listado, crear, editar, eliminar.
- **Métodos de pago:** listado, crear, editar, eliminar.
- **Clientes:** listado, editar, eliminar.
- **Ventas:** listado, detalle, validar pago.
- **Cierre de caja:** listado, nuevo, detalle.
- **Reportes:** `reportes/`.
- **Promociones:** listado, crear, editar, eliminar.

Cada ruta apunta a una función en `views.py` y tiene un `name` para `{% url 'nombre' %}` en plantillas.

---

### 4.7 `gestion/views.py`

**Qué hace:** Contiene la **lógica de cada página y API** (más de 1600 líneas). Resumen por bloques:

- **Helpers y login:** `_ensure_default_user`, `login_view` (con “recordarme” y sesión 2 semanas), `logout_view`.
- **Cuenta/Admin (staff):** `admin_index`, `cuenta_cambiar_password`, `admin_cambiar_password_vendedor`, `admin_usuarios_index`, `admin_usuarios_crear`, `admin_usuarios_eliminar`.
- **Dashboard:** `index` (resumen, ventas recientes, alertas de stock bajo).
- **POS:** `_get_cliente_mostrador`, `_precio_con_promocion`, `pos_view` (productos con precios y promos), `pos_procesar_pago` (crear venta, detalles, pagos, tipo ticket/factura), `pos_buscar_clientes`, `pos_crear_cliente`.
- **Clientes:** `cliente_index`, `cliente_editar`, `cliente_eliminar`.
- **Productos (staff):** `producto_index` (búsqueda, alerta stock), `producto_crear`, `producto_editar`, `producto_eliminar`.
- **Categorías (staff):** `categoria_index`, `categoria_crear`, `categoria_editar`, `categoria_eliminar`.
- **Métodos de pago (staff):** `metodopago_index`, `metodopago_crear`, `metodopago_editar`, `metodopago_eliminar`.
- **Promociones (staff):** `_parse_datetime_local`, `promocion_index`, `promocion_crear`, `promocion_editar`, `promocion_eliminar`.
- **Ventas:** `venta_index`, `venta_detail` (detalle e impresión ticket/factura), `pago_validar`.
- **Cierre de caja:** `cierre_caja_index`, `cierre_caja_nuevo`, `cierre_caja_detail`.
- **Reportes (staff):** `reportes_index`.

Las vistas usan `@login_required` y, donde aplica, `@staff_required` del módulo `decorators`.

---

### 4.8 `gestion/templatetags/gestion_extras.py`

**Qué hace:** Define un **filtro de plantilla** `modo_consumo_safe(venta)` que devuelve `venta.modo_consumo` o `'local'` si no existe (compatibilidad con ventas antiguas). Se usa en plantillas con `{% load gestion_extras %}`.

---

### 4.9 `gestion/management/commands/`

**Qué hace:** Comandos personalizados de `manage.py`.

- **`backup_db.py`:**  
  `python manage.py backup_db` (opcional `--dir=...`). Si la BD es SQLite, copia `db.sqlite3` a la carpeta de backups con timestamp. Si es MySQL, usa `mysqldump` para generar un volcado. Crea la carpeta de backups si no existe.

- **`reset_usuarios.py`:**  
  `python manage.py reset_usuarios`. Crea o actualiza usuarios `admin` (contraseña `admin123`, staff, superuser) y `vendedor` (contraseña `vendedor123`, no staff). Útil para recuperar acceso al sistema.

---

### 4.10 `gestion/migrations/`

**Qué hace:** Migraciones de Django que crean y modifican tablas según los modelos.

- `0001_initial.py`: Crea Categoria, Producto, Cliente, MetodoPago, Promocion, Venta, DetalleVenta, Pago.
- `0002_cierrecaja_cierre_caja.py`: CierreCaja y CierreCajaDetallePago.
- `0003_venta_modo_consumo.py`: Campo modo_consumo en Venta.
- `0004_venta_tipo_documento_numero_factura.py`: tipo_documento y numero_factura en Venta.

Se ejecutan con `python manage.py migrate`.

---

### 4.11 `gestion/static/gestion/`

**Qué hace:** Archivos **estáticos** de la app (CSS, JS, imágenes).

- **`css/base.css`:** Estilos globales (sidebar, colores Panchita, alertas, formularios, tablas).
- **`css/pos.css`:** Estilos del POS (grid de productos, carrito, modal de pago, botones).
- **`js/pos.js`:** Lógica del POS en el navegador: búsqueda por categoría, añadir/quitar ítems del carrito, cantidades, totales, envío del carrito al endpoint de procesar pago, búsqueda y creación de clientes, manejo del modal de pago (ticket/factura, métodos de pago).
- **`img/placeholder-product.png`:** Imagen por defecto cuando un producto no tiene imagen.

---

### 4.12 `gestion/templates/`

**Qué hace:** Plantillas HTML (Django template language). La mayoría extienden `gestion/base.html` (layout con sidebar y bloque `content`).

- **`404.html`, `500.html`:** Páginas de error personalizadas.
- **`gestion/base.html`:** Estructura común: sidebar (Inicio, POS, Ventas, Clientes, Cierre de caja; si staff: Productos, Categorías, Métodos de pago, Promociones, Reportes; Admin, Salir), zona de mensajes y `{% block content %}`.
- **`gestion/login.html`:** Formulario de login (usuario, contraseña, “recordarme”).
- **`gestion/index.html`:** Dashboard (resumen, ventas recientes, alertas de stock).
- **`gestion/pos.html`:** Punto de venta: productos por categoría, carrito, cliente, botón Promociones, modal de pago (ticket/factura, métodos de pago).
- **`gestion/cliente_index.html`, cliente_form.html, cliente_eliminar.html:** Listado, edición y confirmación de eliminación de clientes.
- **`gestion/producto_index.html`, producto_form.html, producto_eliminar.html:** Listado con búsqueda y margen %, formulario y eliminación de productos.
- **`gestion/categoria_index.html`, categoria_form.html, categoria_eliminar.html:** CRUD de categorías.
- **`gestion/metodopago_index.html`, metodopago_form.html, metodopago_eliminar.html:** CRUD de métodos de pago.
- **`gestion/promocion_index.html`, promocion_form.html, promocion_eliminar.html:** CRUD de promociones (vigencia, productos, descuento %).
- **`gestion/venta_index.html`:** Lista de ventas (filtros, enlace al detalle).
- **`gestion/venta_detail.html`:** Detalle de venta (ticket o factura), impresión, validación de pagos.
- **`gestion/cierre_caja_index.html`, cierre_caja_nuevo.html, cierre_caja_detail.html:** Listado, creación y detalle de cierre de caja.
- **`gestion/reportes_index.html`:** Página de reportes (staff).
- **`gestion/admin_index.html`:** Página de administración (cuenta): cambiar contraseña, cambiar contraseña de vendedor, gestión de usuarios.
- **`gestion/admin_usuarios_index.html`, admin_usuarios_crear.html, admin_usuarios_eliminar.html`:** Listado, creación y eliminación de usuarios (staff).
- **`gestion/admin_cambiar_password_vendedor.html`:** Formulario para que admin cambie contraseña de un vendedor.
- **`gestion/cuenta_cambiar_password.html`:** Formulario para que el usuario actual cambie su contraseña.

---

## 5. Flujo de ejecución resumido

1. **Arranque:**  
   `start.sh` o `start.bat` (o directamente `docker-compose up` / `python manage.py runserver`).  
   Si es local con SQLite: `DJANGO_USE_SQLITE=1`, migraciones y `runserver`.

2. **Petición HTTP:**  
   Entra por `panchita_project/urls.py`. Las rutas que no son `admin/` pasan a `gestion/urls.py`.

3. **Vista:**  
   `gestion/views.py` recibe la petición, usa modelos en `gestion/models.py`, aplica `@login_required` y `@staff_required` cuando corresponde, y devuelve una respuesta (HTML renderizado con una plantilla de `gestion/templates/` o JSON para el POS).

4. **Plantillas:**  
   Cargan `base.html`, estáticos de `gestion/static/gestion/` y, en el POS, `pos.js` para el comportamiento en el navegador (carrito, pago, clientes).

5. **Datos:**  
   Persistidos en MySQL (Docker o externo) o SQLite según `settings.py` y variables de entorno. Los comandos `migrate`, `backup_db` y `reset_usuarios` actúan sobre esa base de datos.

Con esta revisión tienes una explicación **carpeta por carpeta y archivo por archivo** de qué se está realizando o ejecutando en el proyecto Panchita.
