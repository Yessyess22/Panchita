# Revisión del Código - Pollos Panchita

## 1. Redundancias y código no utilizado

### Modelos

| Elemento | Estado | Recomendación |
|----------|--------|---------------|
| **Pago.referencia** | Campo en modelo, ya no se usa en la UI | Mantener (opcional en admin). Si no se usará nunca, se puede eliminar con migración. |
| **Promocion.aplicar_a_producto()** | Método definido pero nunca llamado | `_precio_con_promocion()` en views hace la lógica directamente. Se puede eliminar el método o usarlo en `_precio_con_promocion` para evitar duplicar lógica. |

### Archivos

| Archivo | Estado | Recomendación |
|---------|--------|---------------|
| **settings_sqlite.py** | Alternativa a `settings.py` con SQLite | Redundante: `settings.py` ya usa `DJANGO_USE_SQLITE=1`. Se puede eliminar o dejar como referencia. |
| **placeholder-product.png** | Imagen en `static/gestion/img/` | No referenciada en el código. Eliminar o usar como fallback cuando un producto no tiene imagen. |
| **load_products.py** vs **init_data.py** | Dos scripts de carga de datos | `init_data.py`: categorías, métodos de pago, usuarios, cliente Mostrador, productos básicos. `load_products.py`: productos con imágenes desde `media/productos/`. Se solapan en productos. Mantener ambos pero documentar cuándo usar cada uno. |

### CSS (base.css)

| Clase | Uso | Recomendación |
|-------|-----|---------------|
| `.btn-primary`, `.btn-success`, `.btn-danger` | Pocas referencias; muchos botones usan estilos inline | Mantener como utilidades. Opcional: migrar botones a estas clases para unificar estilos. |
| `.card`, `.card-header` | No usadas en templates | Código muerto. Eliminar o dejar para futuras vistas. |
| `.table`, `.table th`, `.table td` | `venta_index` y `cierre_caja_index` usan `.table-header` y `.table-row` (estilos propios) | `.table` no se usa. Eliminar o adaptar las vistas para usarla. |

---

## 2. Lo que falta para usar la página

### Setup inicial (primera vez)

1. **Migraciones**
   ```bash
   ./migrar.sh
   # o: export DJANGO_USE_SQLITE=1 && python manage.py migrate
   ```

2. **Datos iniciales**
   ```bash
   python manage.py shell < init_data.py
   ```
   Crea: categorías, métodos de pago, usuarios (admin/admin123, vendedor/vendedor123), cliente Mostrador, productos básicos.

3. **Productos con imágenes** (opcional)
   ```bash
   python load_products.py
   ```
   Requiere imágenes en `media/productos/`. Actualiza o crea productos con imágenes.

4. **Arrancar servidor**
   ```bash
   ./run_local.sh
   # o: export DJANGO_USE_SQLITE=1 && python manage.py runserver
   ```

### Funcionalidades pendientes o incompletas

| Funcionalidad | Estado | Prioridad |
|---------------|--------|-----------|
| **Cancelar venta** | No hay vista/botón para pasar una venta a "Cancelado" | Media: útil para ventas pendientes o errores |
| **Venta pendiente en POS** | Si el método requiere validación, la venta queda pendiente; no hay flujo claro para completarla o cancelarla | Media |
| **Crear cliente en POS** | El formulario rápido existe; falta validar NIT/CI cuando se elige Factura | Baja |
| **Promociones en la app** | Solo se gestionan en Django Admin; no hay UI propia en la app | Baja |
| **NIT de empresa en facturas** | `EMPRESA_NIT` en settings está comentado; las facturas no muestran NIT del negocio | Baja |
| **Documentación de setup** | README habla de Docker/MySQL; el flujo real usa SQLite y `migrar.sh` | Media |

### Checklist para poner en producción

- [ ] Ejecutar `./migrar.sh` (o migraciones con la BD elegida)
- [ ] Ejecutar `init_data.py` para datos iniciales
- [ ] (Opcional) Ejecutar `load_products.py` si hay imágenes
- [ ] Definir `DEBUG=False`, `DJANGO_SECRET_KEY` y `ALLOWED_HOSTS` en entorno
- [ ] Cambiar contraseñas por defecto (admin123, vendedor123)
- [ ] Configurar `EMPRESA_NIT` en settings si se usan facturas
- [ ] Revisar que existan categorías y métodos de pago activos

---

## 3. Resumen de acciones sugeridas

### Limpieza (opcional)

1. Eliminar `Promocion.aplicar_a_producto()` o usarlo en `_precio_con_promocion`.
2. Eliminar `settings_sqlite.py` si se usa solo `DJANGO_USE_SQLITE`.
3. Eliminar `placeholder-product.png` o usarlo como imagen por defecto.
4. Limpiar CSS no usado en `base.css` (`.card`, `.table` si no se usan).

### Mejoras recomendadas

1. Añadir botón "Cancelar venta" en el detalle de ventas pendientes.
2. Actualizar README con el flujo real: SQLite, `migrar.sh`, `init_data.py`, `run_local.sh`.
3. Validar NIT/CI al crear cliente desde el POS cuando el tipo de documento es Factura.
4. Documentar en README cuándo usar `init_data.py` y cuándo `load_products.py`.
