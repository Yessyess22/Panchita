# Instrucciones para Usar con Docker Compose

## Requisitos Previos

- Docker Desktop instalado y ejecutándose
- Docker Compose (incluido con Docker Desktop)

## Paso 1: Levantar los Contenedores

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
cd "c:\Users\LOQ LENOVO\Documents\UPDS\Tecnologia Web I\actividad3"
docker-compose up -d --build
```

Esto construirá una imagen personlizada con las extensiones necesarias (mysqli, mod_rewrite) y levantará 3 servicios:
- **Apache + PHP 8.2** (puerto 8080)
- **MySQL 8.0** (puerto 3306)
- **phpMyAdmin** (puerto 8081)

## Paso 2: Verificar que los Contenedores Estén Corriendo

```bash
docker-compose ps
```

Deberías ver 3 contenedores activos.

## Paso 3: Importar la Base de Datos

### Opción 1: Usando phpMyAdmin (Recomendado)

1. Accede a phpMyAdmin: `http://localhost:8081`
2. Credenciales:
   - **Servidor:** `mysql`
   - **Usuario:** `root`
   - **Contraseña:** `root`
3. Selecciona la base de datos `lamp` (debería estar creada automáticamente)
4. Ve a la pestaña "Importar"
5. Selecciona el archivo `database.sql`
6. Haz clic en "Continuar"

### Opción 2: Usando la Línea de Comandos

```bash
# Copiar el archivo SQL al contenedor
docker cp database.sql mysql:/tmp/

# Ejecutar el script SQL
docker exec -i mysql mysql -uroot -proot lamp < database.sql
```

## Paso 4: Acceder a la Aplicación

Abre tu navegador y ve a:

```
http://localhost:8080
```

¡Deberías ver la página de inicio con el nuevo diseño Bootstrap 5!

## Comandos Útiles de Docker

### Ver logs de los contenedores
```bash
docker-compose logs -f
```

### Detener los contenedores
```bash
docker-compose down
```

### Reiniciar los contenedores
```bash
docker-compose restart
```

### Acceder al contenedor de MySQL
```bash
docker exec -it mysql bash
mysql -uroot -proot lamp
```

### Acceder al contenedor de Apache
```bash
docker exec -it apache bash
```

## Configuración de la Base de Datos

La aplicación está configurada para conectarse a Docker con:

- **Host:** `mysql` (nombre del contenedor)
- **Usuario:** `user`
- **Contraseña:** `password`
- **Base de datos:** `lamp`
- **Puerto:** 3306 (por defecto)

## Solución de Problemas

### Los contenedores no inician
```bash
# Ver logs de errores
docker-compose logs

# Limpiar y reiniciar
docker-compose down
docker-compose up -d
```

### Error de conexión a la base de datos
- Verifica que el contenedor MySQL esté corriendo: `docker-compose ps`
- Verifica los logs: `docker-compose logs mysql`
- Asegúrate de que la base de datos `lamp` exista

### Puerto 8080 ya está en uso
Edita `docker-compose.yml` y cambia el puerto:
```yaml
ports:
  - "8090:80"  # Cambia 8080 por 8090
```

## Características del Nuevo Diseño

### ✅ Bootstrap 5
- Diseño responsive y moderno
- Componentes profesionales
- Animaciones suaves

### ✅ Colores de Marca
- Amarillo: #f8d210
- Rojo: #dc3545
- Aplicados consistentemente en toda la aplicación

### ✅ Funcionalidades Mejoradas
- Cálculo automático de precios en pedidos
- Validación de stock en tiempo real
- Badges de estado con colores
- Estadísticas en tiempo real
- Diseño responsive (móvil, tablet, desktop)

## Acceso a los Servicios

- **Aplicación Web:** http://localhost:8080
- **phpMyAdmin:** http://localhost:8081
- **MySQL (desde host):** localhost:3306

## Credenciales

### MySQL (root)
- Usuario: `root`
- Contraseña: `root`

### MySQL (usuario app)
- Usuario: `user`
- Contraseña: `password`

### phpMyAdmin
- Servidor: `mysql`
- Usuario: `root`
- Contraseña: `root`
