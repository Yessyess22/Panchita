# Panchita App - Sistema de Gestión de Ventas

> Aplicación web desarrollada con Django para la gestión de ventas de Pollos Panchita

## Descripción del Proyecto

Sistema web integral para la gestión de productos, ventas, clientes y pagos, diseñado con Django y MySQL. El proyecto implementa operaciones CRUD completas con validaciones de negocio y manejo de relaciones entre entidades.

## Tecnologías

- **Backend:** Django 5.0 + Python 3.x
- **Base de Datos:** MySQL 8.0
- **Containerización:** Docker + Docker Compose
- **Frontend:** HTML, CSS, Bootstrap 5

## Características Principales

### Módulos Implementados

1. **Gestión de Productos**
   - Estructura de precios mejorada (costo, precio_venta, descuento)
   - Control de inventario (stock)
   - Cálculo automático de precio final con descuentos
   - Cálculo de margen de ganancia

2. **Gestión de Clientes**
   - Registro completo de clientes
   - Información de contacto
   - Historial de compras

3. **Gestión de Ventas**
   - Creación de ventas con múltiples productos
   - Cálculo automático de totales y descuentos
   - Estados de venta (pendiente, completado, cancelado)
   - Detalles de venta con descuentos por producto

4. **Métodos de Pago**
   - Efectivo
   - Tarjeta de Crédito/Débito
   - Código QR
   - Transferencia Bancaria
   - Validación automática o manual según el método

5. **Sistema de Pagos**
   - Registro de pagos por venta
   - Validación de pagos
   - Control de pagos completos
   - Referencia de transacciones

6. **Promociones**
   - Creación de promociones con fechas de vigencia
   - Aplicación de descuentos a productos específicos
   - Validación automática de vigencia

## Instalación y Configuración

### Requisitos Previos

- Docker y Docker Compose instalados
- Python 3.x (si se ejecuta sin Docker)
- MySQL 8.0 (si se ejecuta sin Docker)

### Opción 1: Usando Docker (Recomendado)

```bash
# 1. Iniciar la base de datos
docker compose up -d db

# 2. Esperar a que MySQL esté listo (aproximadamente 30 segundos)
docker compose logs -f db

# 3. Crear y aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 4. Crear datos iniciales
python manage.py shell < init_data.py

# 5. Crear superusuario (opcional)
python manage.py createsuperuser

# 6. Iniciar el servidor de desarrollo
# Solo esta máquina:
python manage.py runserver

# Para que otras PCs en la red puedan entrar (recomendado en local):
python manage.py runserver 0.0.0.0:8000
```

### Opción 2: Sin Docker

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
export DB_HOST=localhost
export DB_NAME=panchita_db
export DB_USER=tu_usuario
export DB_PASSWORD=tu_password

# 4. Crear y aplicar migraciones
python manage.py makemigrations
python manage.py migrate

# 5. Crear datos iniciales
python manage.py shell < init_data.py

# 6. Iniciar servidor
python manage.py runserver
```

## Subir y clonar el proyecto (GitHub)

Para que **lo que ves en tu PC se vea igual al clonar en otra**:

### 1. Siempre subir los cambios a GitHub

Después de modificar código, estilos o archivos, **debes hacer commit y push**. Si no haces push, GitHub no tiene tus cambios y al clonar se verá la versión antigua.

```bash
cd PanchitaApp   # o la carpeta donde está el proyecto (donde está manage.py)
git add -A
git commit -m "Descripción de los cambios"
git push origin main
```

Hasta que ejecutes `git push origin main`, **nadie que clone el repo verá tus últimas actualizaciones**.

### 2. Al clonar en otra PC

```bash
git clone https://github.com/Yessyess22/Panchita.git
cd Panchita
```

La carpeta `Panchita` tendrá todo el proyecto (manage.py, gestion/, media/, etc.). Luego:

```bash
python3 -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py reset_usuarios
python manage.py runserver
```

Abre `http://localhost:8000`. Si ya habías clonado antes y quieres la última versión:

```bash
cd Panchita
git pull origin main
```

Luego reinicia el servidor y, si hace falta, recarga la página con **Ctrl+Shift+R** (recarga forzada sin caché) para ver los estilos y cambios nuevos.

---

## Acceso a la Aplicación

- **Aplicación Web (en esta máquina):** <http://localhost:8000>
- **Desde otra máquina en la red:** <http://IP-DE-ESTA-MÁQUINA:8000> (ver más abajo)
- **Panel de Administración:** <http://localhost:8000/admin>

### Credenciales por Defecto

**Administrador:**

- Usuario: `admin`
- Contraseña: `admin123`

**Vendedor / Cajero:**

- Usuario: `vendedor`
- Contraseña: `vendedor123`

### Si no puedes ingresar (vendedor o admin)

Si el usuario o la contraseña no funcionan, restablece los usuarios con:

```bash
cd PanchitaApp
python manage.py reset_usuarios
```

Luego intenta de nuevo con `admin` / `admin123` o `vendedor` / `vendedor123`.

También puedes ejecutar de nuevo los datos iniciales (crea categorías, productos, etc. si no existen):

```bash
python manage.py shell < init_data.py
```

### Acceso desde otra máquina (misma red)

Para que otra PC o tablet pueda abrir la app en el navegador:

1. **Iniciar el servidor escuchando en todas las interfaces** (no solo localhost):

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

   Si solo usas `python manage.py runserver`, la app solo responde en la misma PC (localhost).

2. **Averiguar la IP** de la máquina donde corre el servidor:
   - Windows: `ipconfig` → busca "Dirección IPv4"
   - Mac/Linux: `ifconfig` o `ip addr`

3. **En la otra máquina**, en el navegador abre: `http://IP:8000`  
   Ejemplo: si la IP es 192.168.1.10 → `http://192.168.1.10:8000`

4. **Firewall:** si no carga, revisa que el puerto 8000 esté permitido en el firewall de la PC donde corre el servidor.

## Estructura de la Base de Datos

### Modelos Principales

1. **Categoria** - Categorías de productos
2. **Producto** - Productos con estructura de precios mejorada
3. **Cliente** - Información de clientes
4. **MetodoPago** - Métodos de pago disponibles
5. **Promocion** - Promociones con vigencia
6. **Venta** - Ventas con totales y descuentos
7. **DetalleVenta** - Detalles de productos en cada venta
8. **Pago** - Pagos asociados a ventas

### Características de los Modelos

**Producto:**

- `costo`: Precio de compra/producción
- `precio_venta`: Precio de venta al público
- `descuento`: Porcentaje de descuento (0-100)
- `precio_final()`: Método que calcula el precio con descuento
- `margen_ganancia()`: Método que calcula el margen de ganancia

**Venta:**

- `subtotal`: Total antes de descuentos
- `descuento_total`: Total de descuentos aplicados
- `total`: Total final
- `calcular_totales()`: Recalcula automáticamente los totales
- `tiene_pago_completo()`: Verifica si está completamente pagada

**Pago:**

- `validar_pago()`: Valida el pago y actualiza el estado de la venta
- `clean()`: Validaciones para evitar pagos excesivos

## Datos Iniciales

El script `init_data.py` crea:

- 3 Categorías (Pollos, Bebidas, Extras)
- 4 Productos (Chiquitin, Chipollo, Escolar, Panchita)
- 4 Métodos de Pago (Efectivo, Tarjeta, QR, Transferencia)
- 2 Usuarios (admin, vendedor)
- 1 Cliente de ejemplo

## Panel de Administración

El panel de administración de Django incluye:

- Gestión completa de todos los modelos
- Filtros y búsquedas avanzadas
- Visualización de relaciones
- Validaciones automáticas
- Cálculos en tiempo real

## Comandos Útiles

```bash
# Ver migraciones
python manage.py showmigrations

# Crear nueva migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Acceder a shell de Django
python manage.py shell

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic
```

## Docker Compose

El archivo `docker-compose.yml` define:

- **db**: Contenedor MySQL 8.0 (puerto 3309)
- **web**: Aplicación Django (puerto 8000)

```bash
# Iniciar servicios
docker compose up -d

# Ver logs
docker compose logs -f

# Detener servicios
docker compose down

# Reiniciar servicios
docker compose restart
```

## Estructura del Proyecto

```
PanchitaApp/
├── gestion/                    # Aplicación Django principal
│   ├── models.py              # Modelos de datos
│   ├── views.py               # Vistas
│   ├── admin.py               # Configuración del admin
│   ├── urls.py                # URLs de la aplicación
│   └── templates/             # Templates HTML
│       └── gestion/
│           ├── base.html
│           ├── index.html
│           ├── producto_form.html
│           ├── producto_index.html
│           └── venta_form.html
├── panchita_project/          # Configuración del proyecto
│   ├── settings.py            # Configuración Django
│   ├── urls.py                # URLs principales
│   └── wsgi.py                # WSGI config
├── docker-compose.yml         # Configuración Docker
├── Dockerfile                 # Imagen Docker
├── requirements.txt           # Dependencias Python
├── init_data.py              # Script de datos iniciales
└── manage.py                  # CLI de Django
```

## Mejoras Implementadas

### Base de Datos

- ✅ Estructura de precios mejorada (costo, precio_venta, descuento)
- ✅ Sistema de métodos de pago
- ✅ Sistema de promociones con vigencia
- ✅ Sistema de pagos con validaciones
- ✅ Cálculo automático de totales y descuentos

### Funcionalidades

- ✅ Validación de stock
- ✅ Cálculo de margen de ganancia
- ✅ Validación de pagos
- ✅ Control de pagos completos
- ✅ Aplicación automática de descuentos

### Interfaz

- ✅ Formularios mejorados con validaciones
- ✅ Selección de método de pago en ventas
- ✅ Visualización de precios con descuentos
- ✅ Panel de administración completo

## Autor

**Proyecto Académico**

- Materia: Tecnología Web I
- Institución: UPDS (Universidad Privada Domingo Savio)

---

**Última actualización:** 2026-01-21
