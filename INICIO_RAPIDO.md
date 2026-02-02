# 🚀 Pollos Panchita - Inicio Rápido

**Un solo comando para arrancar el proyecto**

---

## ⚡ Ejecutar el Proyecto

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Windows
```cmd
start.bat
```

**Eso es todo.** El script hace TODO automáticamente.

---

## 🤔 ¿Qué hace el script?

El script detecta automáticamente tu entorno:

### Si tienes Docker instalado:
- ✅ Usa Docker (NO requiere Python ni pip)
- ✅ MySQL + Django en contenedores
- ✅ Red configurada: 192.168.100.0/24
- ✅ Acceso: http://localhost:8000

**Te pregunta cómo iniciar:**
1. Primer inicio / Reconstruir (recomendado)
2. Inicio rápido
3. Segundo plano
4. Detener contenedores
5. Ver estado

### Si NO tienes Docker:
- ✅ Usa SQLite local (requiere Python + pip)
- ✅ Detecta Python automáticamente
- ✅ Instala dependencias si faltan
- ✅ Ejecuta migraciones
- ✅ Acceso: http://127.0.0.1:8000

---

## 📋 Requisitos

### Opción 1: Con Docker (Recomendado)
**Solo necesitas:**
- Docker Desktop

**Instalar:**
- Windows/Mac: https://www.docker.com/products/docker-desktop
- Linux: https://docs.docker.com/engine/install/

### Opción 2: Sin Docker
**Necesitas:**
- Python 3.8+
- pip

**Instalar:**
- Windows: https://python.org (marca "Add to PATH")
- Mac: `brew install python`
- Linux: `sudo apt install python3 python3-pip`

---

## 🌐 Acceso

### Con Docker:
- Aplicación: http://localhost:8000
- Admin: http://localhost:8000/admin
- MySQL: localhost:3309

### Sin Docker (SQLite):
- Aplicación: http://127.0.0.1:8000
- Admin: http://127.0.0.1:8000/admin

---

## 🔧 Problemas Comunes

### "Docker no está corriendo"
→ Inicia Docker Desktop

### "Python no encontrado"
→ Instala Python desde python.org

### "Permission denied" (Linux/Mac)
```bash
chmod +x start.sh
```

---

## 📊 Docker vs Local

| | Docker | Local |
|---|--------|-------|
| Instalación | Solo Docker | Python + pip |
| Base de datos | MySQL 8.0 | SQLite |
| Aislamiento | Total | Sistema |
| Red | 192.168.100.0/24 | N/A |

---

## 🎯 Recomendación

**Primera vez:** Instala Docker Desktop y ejecuta `./start.sh` o `start.bat`

Es más simple y no contamina tu sistema con dependencias de Python.
