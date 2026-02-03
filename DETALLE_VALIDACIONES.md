# Detalle de validaciones del proyecto Panchita

Revisión de **todas las validaciones** actuales y de **qué falta** para que la aplicación sea considerada profesional (integridad de datos, unicidad, rangos, consistencia y UX). **No se ha modificado ningún código**; solo se documenta el estado actual y las recomendaciones.

---

## 1. Resumen ejecutivo

| Área | Estado actual | Gaps importantes |
|------|----------------|-------------------|
| **Modelos (BD)** | Algunos `unique`, validadores numéricos, un `clean()` en Pago, `unique_together` en CierreCajaDetallePago | Producto sin unique en nombre; Promocion sin unique ni validación de fechas en modelo; Venta.numero_factura sin unique; Pago.clean() no se invoca al crear desde POS |
| **Vistas (lógica)** | Validaciones manuales en crear/editar para categoría, método de pago, cliente (CI/NIT), usuario (username), promoción (fechas) | Producto: no se valida nombre duplicado; Cliente: email sin formato; longitud de textos no validada; pocos try/except para IntegrityError |
| **Formularios / APIs** | Campos requeridos y rangos en vistas | Sin validación de tipo/tamaño de imagen; sin límite de longitud en frontend/backend para algunos campos |

A continuación se detalla por modelo y por flujo.

---

## 2. Validaciones en modelos (base de datos)

### 2.1 Lo que ya está bien

- **Llave primaria:** En todos los modelos Django usa `id` (AutoField) como PK; es única por definición. No hay que cambiar nada.
- **Categoria:** `nombre` con `unique=True` → no pueden existir dos categorías con el mismo nombre.
- **Cliente:** `ci_nit` con `unique=True` (nullable) → no pueden existir dos clientes con el mismo CI/NIT.
- **MetodoPago:** `nombre` con `unique=True` → no pueden existir dos métodos de pago con el mismo nombre.
- **CierreCajaDetallePago:** `unique_together = [['cierre', 'metodo_pago']]` → en un mismo cierre no puede repetirse el mismo método de pago.
- **Validadores numéricos en modelos:**  
  Producto (costo, precio_venta ≥ 0.01; descuento 0–100; stock ≥ 0), Promocion (descuento_porcentaje 0.01–100), DetalleVenta (cantidad ≥ 1, descuento_porcentaje 0–100), Pago (monto ≥ 0.01), CierreCaja y CierreCajaDetallePago (montos ≥ 0).
- **Pago.clean():** Valida que la suma de pagos de la venta no exceda el total. **Problema:** en el proyecto no se llama a `full_clean()` antes de `Pago.objects.create()` en `pos_procesar_pago`, por lo que esta validación **nunca se ejecuta** al crear el pago desde el POS (ahora el pago es único por venta y igual al total, pero si en el futuro se permiten pagos parciales, sería crítico).

### 2.2 Lo que falta o es débil a nivel modelo

| Modelo | Campo / regla | Situación | Recomendación para nivel profesional |
|--------|----------------|-----------|--------------------------------------|
| **Producto** | `nombre` | Sin `unique=True`. Pueden existir varios productos con el mismo nombre (ej. "Coca Cola 500ml" y "Coca Cola 500ml" duplicado). | Valorar `unique=True` si el negocio exige nombre único; si se permite repetir (ej. por presentación), al menos **unique junto a categoría** o **validación en vista** para evitar duplicados no deseados. |
| **Promocion** | `nombre` | Sin `unique`. Pueden existir dos promociones con el mismo nombre. | Según negocio: `unique=True` o validación en vista (ej. mismo nombre solo si no se solapan en fechas). |
| **Promocion** | `fecha_fin` > `fecha_inicio` | No hay validación en el modelo (solo en vistas). | Añadir `clean()` en el modelo que levante `ValidationError` si `fecha_fin <= fecha_inicio`, para que la regla quede centralizada y se cumpla también desde el admin. |
| **Venta** | `numero_factura` | Sin `unique` ni `UniqueConstraint`. La numeración se asigna en vista con `Max() + 1`. En concurrencia, dos requests podrían obtener el mismo `numero_factura`. | Para facturación seria: restricción única en BD, p. ej. `UniqueConstraint(fields=['tipo_documento', 'numero_factura'], condition=Q(tipo_documento='factura')` o campo único cuando no es null, y generación del número en transacción (select for update o bloqueo). |
| **Cliente** | `nombre_completo` | Sin unique. Pueden existir varios clientes con el mismo nombre (habitual y a veces deseable). | No suele ser obligatorio en modelo; si se quiere evitar duplicados “claros”, puede hacerse validación en vista (ej. mismo nombre + mismo CI/NIT = duplicado). |
| **Cliente** | `email` | Sin validación de formato en modelo (Django solo asegura que sea un string válido para EmailField). | El formato lo valida Django a nivel BD; en vistas no se valida formato antes de guardar. Para profesional: validar formato (regex o validadores) en vista o en `clean()` del modelo. |
| **User (Django)** | `username` | Ya es unique por defecto. La vista `admin_usuarios_crear` comprueba con `filter(username=...).exists()` antes de crear. | Correcto. Opcional: capturar `IntegrityError` por si dos requests crean el mismo usuario a la vez y devolver mensaje amigable. |

---

## 3. Validaciones en vistas (lógica de negocio)

### 3.1 Donde ya se valida bien

- **Login:** Usuario vacío, contraseña, cuenta desactivada, “recordarme”.
- **Cambio de contraseña (cuenta y admin):** Contraseña actual, nueva obligatoria, longitud ≥ 8, coincidencia de confirmación.
- **Usuarios (crear):** Usuario obligatorio, único (por `exists()`), contraseña obligatoria, longitud, confirmación, rol dentro de opciones.
- **Usuarios (eliminar):** No permitir desactivar la cuenta del propio usuario.
- **Clientes (editar):** Nombre obligatorio, CI/NIT único excluyendo el propio cliente (`exclude(pk=pk)`).
- **Clientes (crear desde POS):** Nombre obligatorio, CI/NIT único.
- **Categorías (crear/editar):** Nombre obligatorio, nombre único (con `nombre__iexact`, insensible a mayúsculas) excluyendo el registro actual en edición.
- **Categorías (eliminar):** No permitir eliminar/desactivar si tiene productos activos.
- **Métodos de pago (crear/editar):** Nombre obligatorio, nombre único (iexact) excluyendo el actual en edición.
- **Productos (crear/editar):** Nombre obligatorio, categoría obligatoria y existente, valores numéricos (costo, precio, descuento, stock) y rangos (costo ≥ 0, precio > 0, descuento 0–100, stock ≥ 0).
- **Promociones (crear/editar):** Nombre obligatorio, descuento 0.01–100, fechas obligatorias, fecha_fin > fecha_inicio.
- **POS (procesar pago):** Cliente y método de pago existentes, ítems no vacíos, factura solo si cliente tiene NIT/CI válido (no Mostrador), producto existente y activo, cantidad entera > 0, stock suficiente, precio coherente con máximo.

### 3.2 Gaps en vistas (recomendaciones para nivel profesional)

| Dónde | Qué falta | Detalle |
|-------|-----------|---------|
| **Producto (crear/editar)** | **Nombre duplicado** | No se comprueba si ya existe otro producto (o otro activo) con el mismo nombre. Si el negocio no quiere duplicados, añadir algo como `Producto.objects.filter(nombre__iexact=nombre).exclude(pk=pk).exists()` y mensaje "Ya existe un producto con ese nombre." |
| **Cliente (crear/editar y POS)** | **Formato de email** | No se valida que `email` sea un email válido (solo que no esté vacío). Recomendación: validar con regex o `EmailValidator` y rechazar o avisar. |
| **Cliente** | **Longitud de campos** | Modelo tiene `max_length` (ej. nombre_completo 150, ci_nit 20). Las vistas no truncan ni validan longitud; si el usuario pega texto muy largo, puede fallar en BD o truncarse sin aviso. Recomendación: validar `len(nombre) <= 150`, etc., y mensaje claro. |
| **Producto** | **Longitud nombre/descripción** | Igual: nombre 100, descripcion sin límite en práctica. Validar longitud de nombre y, si se limita descripción, validar también. |
| **Producto** | **Imagen** | No se valida tipo de archivo (jpeg, png, etc.) ni tamaño máximo. Riesgo: subida de ejecutables o archivos enormes. Recomendación: validar extensión/content-type y tamaño (ej. máximo 2–5 MB). |
| **Promociones** | **Nombre duplicado** | No se comprueba si ya existe una promoción con el mismo nombre. Opcional según negocio; si se quiere evitar, añadir comprobación tipo categoría/método de pago. |
| **Cierre de caja** | **Doble cierre mismo día/usuario** | No se valida si el usuario ya tiene un cierre para la misma fecha. Podría permitir varios cierres por día (por turnos); si la política es “un cierre por usuario por día”, añadir validación o unique en modelo. |
| **Pago (POS)** | **Uso de Pago.clean()** | Al crear el pago con `Pago.objects.create(...)` no se llama `full_clean()`, por lo que la validación de “monto total de pagos no exceda total de la venta” no se ejecuta. Hoy el flujo es un solo pago = total, pero para pagos parciales sería esencial. Recomendación: crear el `Pago`, asignar atributos, llamar `pago.full_clean()` y luego `pago.save()`, o usar un formulario que llame a `full_clean()`. |
| **Venta / Factura** | **IntegrityError por numero_factura** | Si se añade restricción única a `numero_factura`, en concurrencia podría dispararse `IntegrityError`. Las vistas deberían capturarla, hacer rollback si aplica, y mostrar mensaje del tipo "Error al generar número de factura; intente de nuevo." |
| **Usuarios** | **IntegrityError por username** | Si dos peticiones crean el mismo usuario a la vez, `User.objects.create_user(...)` puede lanzar `IntegrityError`. Recomendación: `try/except IntegrityError` y mensaje "El usuario ya existe." |
| **Categoría / MetodoPago** | **IntegrityError por unique** | Si por race condition se inserta un nombre duplicado, la BD lanzará error. Opcional: capturar `IntegrityError` en crear/editar y mostrar mensaje amigable. |

---

## 4. Validaciones por entidad (checklist)

### Categoria

- **Modelo:** `nombre` unique ✅  
- **Vista crear:** nombre obligatorio, no comprueba unique (lo garantiza el modelo) ✅; en edición se comprueba otro con mismo nombre (iexact) ✅  
- **Vista eliminar:** no permite si tiene productos activos ✅  
- **Recomendación:** Opcional capturar `IntegrityError` al crear/editar por si hay concurrencia.

### Producto

- **Modelo:** nombre **no** unique ❌; validadores numéricos y stock ✅  
- **Vista crear/editar:** nombre obligatorio, categoría, rangos numéricos ✅  
- **Vista crear/editar:** **no** se valida nombre duplicado ❌  
- **Imagen:** **no** se valida tipo ni tamaño ❌  
- **Longitud:** **no** se valida longitud de nombre/descripción en vista ❌  
- **Recomendación:** Decidir si nombre debe ser único (o único por categoría); validar duplicados en vista; validar imagen (tipo, tamaño) y longitudes.

### Cliente

- **Modelo:** `ci_nit` unique ✅  
- **Vista editar / POS crear:** nombre obligatorio, CI/NIT único (excluyendo pk en edición) ✅  
- **Email:** **no** se valida formato ❌  
- **Longitud:** **no** se valida en vista (nombre_completo 150, ci_nit 20, etc.) ❌  
- **Recomendación:** Validar formato de email y longitudes; mensaje claro si se supera el límite.

### MetodoPago

- **Modelo:** `nombre` unique ✅  
- **Vista crear/editar:** nombre obligatorio, único (iexact, excluyendo pk) ✅  
- **Vista eliminar:** solo desactiva; **no** comprueba si hay pagos/ventas usando el método ⚠️ (desactivar está bien; eliminar físico sería otro caso).  
- **Recomendación:** Opcional capturar `IntegrityError`; si en el futuro se permite “eliminar” en lugar de desactivar, comprobar que no existan pagos con ese método.

### Promocion

- **Modelo:** nombre **no** unique ❌; descuento_porcentaje con validadores ✅; **no** hay validación de fechas en modelo ❌  
- **Vista crear/editar:** nombre obligatorio, descuento 0.01–100, fechas obligatorias, fecha_fin > fecha_inicio ✅  
- **Vista:** **no** se valida nombre duplicado ❌  
- **Recomendación:** Añadir `clean()` en modelo para fecha_fin > fecha_inicio; opcional unique o validación de nombre duplicado en vista.

### Venta / Factura

- **Modelo:** `numero_factura` **no** tiene restricción única ❌; riesgo de duplicado en concurrencia.  
- **Vista POS:** Se asigna numero_factura con `Max()+1` ✅ pero sin transacción atómica ni unique en BD ❌  
- **Recomendación:** Restricción única en BD para (tipo_documento='factura', numero_factura) y generación del número en transacción; capturar `IntegrityError` y reintentar o informar.

### Pago

- **Modelo:** `clean()` que valida suma de pagos ≤ total de la venta ✅  
- **Vista POS:** Crea pago con `Pago.objects.create(...)` **sin** llamar `full_clean()` ❌ → la validación del modelo no se ejecuta.  
- **Recomendación:** Llamar `full_clean()` antes de guardar (o usar formulario) para que la regla de negocio se aplique siempre, sobre todo si más adelante hay pagos parciales.

### CierreCaja

- **Modelo:** Sin unique por (usuario, fecha).  
- **Vista:** No se valida “un cierre por usuario por día”.  
- **Recomendación:** Solo si el negocio exige un cierre por usuario/día, añadir validación en vista o restricción en modelo.

### Usuarios (User)

- **Modelo (Django):** `username` unique ✅  
- **Vista crear:** username obligatorio, no existe ya, contraseña y confirmación ✅  
- **Recomendación:** Capturar `IntegrityError` al crear usuario y mostrar mensaje amigable.

---

## 5. Priorización sugerida para una página “profesional”

**Alta prioridad (integridad y seguridad)**  
1. **Producto:** Evitar nombres duplicados (unique en modelo o validación en vista según regla de negocio).  
2. **Venta/Factura:** Unicidad de `numero_factura` en BD y generación en transacción; manejo de `IntegrityError`.  
3. **Pago:** Llamar `full_clean()` antes de guardar al crear pagos desde el POS (y en cualquier otro flujo que cree Pagos).  
4. **Imagen de producto:** Validar tipo de archivo y tamaño máximo.

**Prioridad media (calidad de datos y UX)**  
5. **Cliente:** Validar formato de email y longitudes (nombre, CI/NIT, etc.).  
6. **Producto:** Validar longitudes de nombre y descripción.  
7. **Promocion:** `clean()` en modelo para fecha_fin > fecha_inicio; opcional validación de nombre duplicado.  
8. **Manejo de IntegrityError** en crear/editar (Usuario, Categoria, MetodoPago, Cliente) con mensaje claro.

**Prioridad baja (pulido)**  
9. **Cierre de caja:** Política de “un cierre por usuario por día” si aplica.  
10. **Promocion:** Decidir si el nombre debe ser único y aplicar en modelo o vista.

---

## 6. Resumen por “tipo” de validación

| Tipo | Ejemplos actuales | Faltan (recomendado) |
|------|-------------------|------------------------|
| **Unicidad (modelo)** | Categoria.nombre, Cliente.ci_nit, MetodoPago.nombre, unique_together CierreCajaDetallePago | Producto.nombre (o por categoría), Promocion.nombre (opcional), Venta.numero_factura para facturas |
| **Unicidad (vista)** | Usuario, Cliente CI/NIT, Categoria nombre, MetodoPago nombre | Producto nombre, Promocion nombre (opcional) |
| **Rangos numéricos** | En modelo y vista para costo, precio, descuento, stock, promociones | - |
| **Reglas de negocio en modelo** | Pago.clean() (suma pagos ≤ total) | Promocion: fecha_fin > fecha_inicio en clean(); uso efectivo de Pago.clean() vía full_clean() |
| **Obligatoriedad** | Validada en vistas para nombres, categoría, fechas, etc. | - |
| **Formato** | - | Email en Cliente; tipo y tamaño de imagen en Producto |
| **Longitud** | Solo por max_length en BD | Validación explícita en vistas con mensaje claro (nombre, descripción, CI/NIT, etc.) |
| **Concurrencia** | - | Unique en numero_factura + generación atómica; captura de IntegrityError en usuario, categoría, método de pago, factura |

Con esto tienes un **detalle completo** de validaciones actuales y de lo que convendría añadir o ajustar para que la aplicación sea sólida y profesional, sin que se haya modificado aún ningún archivo del proyecto.
