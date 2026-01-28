# Revisión completa del proyecto – Pollos Panchita (POS local)

## Resumen del proyecto actual

La app es un **punto de venta (POS) para local** de comida rápida de pollos. No vende en línea; solo registra ventas en el local. A continuación se revisa lo que ya existe y lo que conviene mejorar o agregar.

---

## Lo que ya tienes (funcional)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| **Login / Logout** | ✅ | Autenticación básica |
| **Inicio (Dashboard)** | ✅ | Resumen del día: total recaudado, ventas hoy, productos vendidos, últimas ventas |
| **Punto de Venta (POS)** | ✅ | Carrito, categorías, búsqueda, pago con cliente y método de pago |
| **Productos** | ✅ | Listar, crear, editar, eliminar (soft delete) |
| **Ventas** | ✅ | Listado con filtros por estado y fecha |
| **Clientes** | ⚠️ | Solo en admin y en select del POS; no hay pantalla de gestión |
| **Categorías** | ⚠️ | Solo en admin |
| **Métodos de pago** | ⚠️ | Solo en admin |
| **Promociones** | ⚠️ | Modelo existe pero no se usa en POS |
| **Admin Django** | ✅ | Gestión de todos los modelos |

---

## Lo que falta o está incompleto

### 1. Roles (Administrador vs Cajero/Vendedor) ✅ IMPLEMENTADO

- **Situación:** Solo existía `login_required`. No se distinguía entre administrador y cajero.
- **Implementado:**
  - **Administrador** (`user.is_staff == True`): acceso a Inicio, POS, Ventas, Productos y Admin (Django).
  - **Cajero/Vendedor** (`user.is_staff == False`): solo Inicio, POS y Ventas (listar/ver). No ve Productos ni Admin.
  - Decorador `@staff_required` en `gestion/decorators.py`; aplicado a producto_index, producto_crear, producto_editar, producto_eliminar y venta_crear.
  - Menú en `base.html`: "Ventas" visible para todos; "Productos" y "Admin" solo si `user.is_staff`.
  - Mensaje de bienvenida en login indica el rol (Administrador / Cajero).
  - Usuarios en `init_data.py`: admin (is_staff=True), vendedor (is_staff=False).

### 2. Navegación y enlace a “Ventas” ✅ IMPLEMENTADO

- **Situación:** En el menú no había enlace a “Ver todas las ventas”.
- **Implementado:** Enlace “Ventas” en `base.html` que apunta a `venta_index`, visible para todos los usuarios logueados.

### 3. Cliente “Mostrador” o venta rápida

- **Situación:** Siempre se exige elegir un cliente.
- **Recomendación:** Tener un cliente fijo “Mostrador” o “Cliente general” y permitir en el POS:
  - Opción “Venta mostrador” (usa ese cliente por defecto).
  - Opción “Elegir cliente” para factura o cliente frecuente.
- Así el cajero no tiene que crear/clientes en cada venta rápida.

### 4. Estadísticas del día (fecha)

- **Situación:** Ha habido problemas con ventas que no se cuentan “hoy”.
- **Recomendación (ya tocado en código):** Usar `fecha__date=hoy` con `timezone.now().date()` y `USE_TZ = True` con `TIME_ZONE = 'America/La_Paz'`. Mantener esa lógica y, si hace falta, un respaldo por “últimas 24 h” solo para diagnóstico, no como lógica principal del negocio.

### 5. Seguridad y producción

- **Situación:** `DEBUG = True`, `ALLOWED_HOSTS = ['*']`, `SECRET_KEY` por defecto.
- **Recomendación:**
  - Producción: `DEBUG = False`, `ALLOWED_HOSTS` con tu dominio o IP.
  - `SECRET_KEY` desde variable de entorno, nunca en el repo.
  - HTTPS en producción.
  - No exponer `/admin/` sin restricción; si solo admin debe entrar, combinar con `is_staff` y fuerte contraseña.

### 6. Backup de base de datos

- **Recomendación:** Script o tarea programada (cron) que haga backup de MySQL (por ejemplo `mysqldump`) cada día, y guardar copias en otro disco o servidor.

---

## Sugerencias de funcionalidades nuevas (priorizadas)

### Prioridad alta (recomendado para un local)

1. **Roles claros**
   - Admin: todo.
   - Cajero: Inicio, POS, ver ventas (sin borrar/editar productos ni ventas).

2. **Cliente “Mostrador”**
   - Un cliente por defecto para ventas rápidas sin elegir cliente cada vez.

3. **Menú “Ventas” en la barra**
   - Enlace visible a la lista de ventas (historial).

4. **Detalle de una venta**
   - Vista de solo lectura de una venta (ítems, totales, pagos, estado) desde tu app, sin depender del admin.

5. **Cierre de caja (opcional pero muy útil)**
   - Al final del turno: total ventas, total por método de pago, y opcionalmente “fondo inicial” y “fondo final”.
   - Puede ser una pantalla “Cierre de caja” con totales del día y botón “Cerrar turno” (guarda un registro de cierre).

### Prioridad media

6. **Gestión de clientes en la app**
   - Listar, crear, editar clientes desde la web (no solo admin), para facturas o programas de fidelidad.

7. **Gestión de categorías en la app**
   - CRUD de categorías para admin (y solo admin), para no depender del admin de Django.

8. **Reportes básicos**
   - Ventas por día / por semana / por mes.
   - Productos más vendidos.
   - Total por método de pago.
   - Todo en pantallas propias de la app, con filtros por fecha.

9. **Promociones en el POS**
   - Si quieres usar promociones: en el POS mostrar “Promociones vigentes” y aplicar descuento al producto o al ticket según regla (por producto o por monto).

10. **Alerta de stock bajo**
    - En dashboard o en lista de productos: aviso cuando `stock < X` (ej. 5 unidades) para reordenar.

### Prioridad baja

11. **Turnos / Usuario que abrió caja**
    - Modelo “Turno” (usuario, fecha/hora apertura, cierre, total ventas). Útil si hay varios cajeros y quieres responsabilidad por caja.

12. **Impresión de ticket**
    - Botón “Imprimir ticket” que abra una vista de impresión (HTML) o envíe a una impresora térmica vía navegador o API.

13. **Categorías en la app (para cajero)**
    - Solo lectura de categorías en POS ya lo tienes; crear/editar categorías solo admin.

14. **Cambio de contraseña**
    - Pantalla “Mi cuenta” para que el usuario cambie su contraseña.

15. **Auditoría simple**
    - En ventas o en productos: guardar “quién y cuándo” modificó (con `user` y `timestamp`). Puede ser un modelo `Auditoria` o campos `modified_by`, `modified_at` en los modelos críticos.

---

## Resumen de mejoras recomendadas (checklist)

- [x] **Roles:** Restringir vistas por rol (admin vs cajero) y ocultar menú según rol.
- [x] **Menú:** Añadir enlace “Ventas” / “Historial” en `base.html`.
- [ ] **Cliente mostrador:** Cliente por defecto y opción “Venta mostrador” en POS.
- [ ] **Detalle de venta:** Vista `venta_detail` (solo lectura) y enlace desde lista de ventas.
- [ ] **Cierre de caja:** Pantalla con totales del día y registro de cierre (opcional).
- [ ] **Clientes en la app:** CRUD de clientes (para admin o también cajero si quieres que registre clientes).
- [ ] **Categorías en la app:** CRUD de categorías solo para admin.
- [ ] **Reportes:** Ventas por período, productos más vendidos, por método de pago.
- [ ] **Stock bajo:** Alerta en dashboard o en productos.
- [ ] **Producción:** `DEBUG=False`, `ALLOWED_HOSTS`, `SECRET_KEY` por entorno, HTTPS.
- [ ] **Backup:** Script de backup de la base de datos.

---

## Estructura sugerida del menú según rol

**Cajero / Vendedor**
- Inicio  
- Punto de Venta  
- Ventas (solo listar y ver detalle)  
- Salir  

**Administrador**
- Todo lo del cajero, más:
- Productos  
- Clientes (si lo implementas)  
- Categorías (si lo implementas)  
- Reportes (si lo implementas)  
- Cierre de caja (si lo implementas)  
- Admin (enlace a `/admin/` solo para staff)  
- Salir  

---

## Conclusión

La base del POS está bien planteada para un local: productos, categorías, ventas, pagos, clientes y POS funcional. Los pasos más importantes para que encaje con “solo local, admin y cajero” son:

1. Definir y aplicar **roles** (admin vs cajero) en vistas y menú.  
2. **Cliente mostrador** y menú **Ventas** visibles.  
3. **Detalle de venta** en la app.  
4. Luego, según necesidad: **cierre de caja**, **reportes**, **gestión de clientes/categorías** en la app, y **seguridad en producción**.

Si indicas por dónde quieres empezar (roles, cliente mostrador, detalle de venta, cierre de caja, etc.), se puede bajar esto a tareas concretas de código (vistas, URLs, templates y permisos) paso a paso.
