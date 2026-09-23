# 🍽️ Sistema de Reservas de Restaurante

Sistema web completo para gestión de reservas de restaurante desarrollado con Django y MongoDB.

## 📋 Características

- ✅ Gestión de clientes y usuarios
- ✅ Sistema de reservas con selección de mesas
- ✅ Panel administrativo completo
- ✅ Generación de facturas
- ✅ Manuales de usuario e instalación integrados
- ✅ Atajos de teclado (F1, F2, F3)
- ✅ Diseño responsive con DaisyUI y Tailwind CSS

## 🚀 Tecnologías Utilizadas

- **Backend:** Django 5.x
- **Base de Datos:** MongoDB
- **ODM:** MongoEngine
- **Frontend:** HTML, CSS, JavaScript, Tailwind CSS, DaisyUI
- **Autenticación:** Django Auth + bcrypt

## 📦 Instalación

### Requisitos Previos

- Python 3.8+
- MongoDB 4.0+
- pip
- virtualenv (recomendado)

### Pasos de Instalación

1. **Clonar el repositorio**

```bash
git clone https://github.com/TU-USUARIO/TU-REPOSITORIO.git
cd TU-REPOSITORIO
```

2. **Crear y activar entorno virtual**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar MongoDB**

Asegúrate de que MongoDB esté corriendo:

```bash
# Windows
net start MongoDB

# Linux
sudo systemctl start mongod
```

5. **Configurar variables de entorno**

Crea un archivo `.env` en la raíz del proyecto (ver `.env.example`):

```env
SECRET_KEY=tu-clave-secreta-aquí
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
MONGODB_NAME=restaurante_db
```

6. **Ejecutar migraciones**

```bash
python manage.py migrate
```

7. **Crear superusuario (opcional)**

```bash
python manage.py createsuperuser
```

8. **Ejecutar el servidor**

```bash
python manage.py runserver
```

Abre tu navegador en: `http://127.0.0.1:8000/`

## 🎯 Uso

### Atajos de Teclado

- **F1** (desde landing): Ir a manuales
- **F2** (en manuales): Abrir Manual de Usuario
- **F3** (en manuales): Abrir Manual de Instalación
- **ESC**: Cerrar modales

### URLs Principales

- `/` - Landing page
- `/clientes/login/` - Login de clientes
- `/clientes/registro/` - Registro de clientes
- `/reservas/` - Gestión de reservas
- `/admin/` - Panel administrativo
- `/manuales/` - Documentación

## 📁 Estructura del Proyecto

```
restaurante_reservas/
├── core/                   # App principal
├── clientes/              # Gestión de clientes
├── reservas/              # Sistema de reservas
├── facturas/              # Generación de facturas
├── admin_panel/           # Panel administrativo
├── manuales/              # Documentación
├── static/                # Archivos estáticos
├── media/                 # Archivos subidos
├── requirements.txt       # Dependencias
├── manage.py             # Script de Django
└── .env.example          # Ejemplo de variables de entorno
```



Tu Nombre - tu@email.com

Link del Proyecto: [https://github.com/TuUsuario/TuRepositorio](https://github.com/TuUsuario/TuRepositorio)
