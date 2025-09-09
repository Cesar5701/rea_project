# 🚀 Plataforma REA - Recursos Educativos Abiertos

## Descripción
Esta es una plataforma web para la gestión de **Recursos Educativos Abiertos (REA)**. Permite a los usuarios registrarse, iniciar sesión, y compartir recursos de aprendizaje. Los recursos son clasificados automáticamente usando modelos de Procesamiento de Lenguaje Natural (NLP) y los archivos se almacenan de forma descentralizada en la red IPFS.

La plataforma también incluye una potente funcionalidad de **búsqueda semántica** utilizando una base de datos vectorial (ChromaDB) y una **sala de comunicación P2P** en tiempo real usando WebRTC.

## ✨ Características Principales
* **Autenticación de Usuarios:** Sistema completo de registro, inicio de sesión y gestión de sesiones con `Flask-Login`.
* **Gestión de Recursos:** Añade, visualiza y gestiona recursos con título, descripción, categoría y archivos.
* **Almacenamiento Descentralizado en IPFS:** Los archivos se suben a IPFS (InterPlanetary File System) usando la API de Web3.Storage, garantizando su persistencia y descentralización.
* **Clasificación Automática con IA:** Utiliza un modelo de clasificación **zero-shot** (`transformers` de Hugging Face) para asignar automáticamente una categoría a cada recurso (p. ej., "programación", "matemáticas", "historia").
* **Búsqueda Semántica:** Los recursos son vectorizados usando *embeddings* de BERT y almacenados en **ChromaDB**. La búsqueda utiliza similitud vectorial para encontrar los recursos más relevantes, entendiendo el significado de la consulta, no solo las palabras clave.
* **Sala de Colaboración P2P:** Incluye una sala de chat y transferencia de archivos en tiempo real entre usuarios usando **WebRTC** y `Flask-SocketIO` para la señalización.
* **Pruebas Automatizadas:** Suite de pruebas con `pytest` y `mocker` para garantizar la fiabilidad del código.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Flask, Flask-Login, Flask-SocketIO
* **Base de Datos Relacional:** SQLite
* **Base de Datos Vectorial:** ChromaDB
* **NLP:** `transformers` (Hugging Face), PyTorch, Numpy
* **Frontend:** HTML, Tailwind CSS, JavaScript
* **Almacenamiento:** IPFS (via Web3.Storage)
* **Comunicación en tiempo real:** WebRTC, Socket.IO
* **Testing:** Pytest

## ⚙️ Instalación

Sigue estos pasos para poner en marcha el proyecto en tu entorno local.

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/Cesar5701/rea_project.git](https://github.com/Cesar5701/rea_project.git)
    cd rea_project
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    # Para Linux/macOS
    python3 -m venv venv
    source venv/bin/activate

    # Para Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
    +   **Nota:** Este comando descargará las librerías de PyTorch y Transformers, que incluyen modelos de lenguaje de varios cientos de megabytes. La primera vez puede tardar un poco.

4.  **Configurar las variables de entorno:**
    Crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables:
    ```ini
    # Clave secreta para proteger las sesiones de Flask.
    SECRET_KEY='una-clave-muy-segura-y-dificil-de-adivinar'

    # Tu token de API de Web3.Storage para poder subir archivos a IPFS.
    WEB3_STORAGE_TOKEN='TU_API_TOKEN_DE_WEB3_STORAGE'
    
    # (Opcional) Ruta a la base de datos. Por defecto es 'rea.db'.
    DATABASE_URL='rea.db'
    ```

5.  **Inicializar la base de datos:**
    Ejecuta este script una sola vez para crear el archivo de la base de datos y las tablas necesarias.
    ```bash
    python init_db.py
    ```

## ▶️ Ejecución

1.  **Iniciar la aplicación:**
    ```bash
    python run.py
    ```
2.  La aplicación se ejecutará en modo de depuración en `http://127.0.0.1:5000`.
    > **Importante:** La primera vez que inicies la aplicación, el script `app/nlp_utils.py` descargará los modelos de Hugging Face. Este proceso puede tardar varios minutos dependiendo de tu conexión a internet. Los inicios posteriores serán instantáneos.

## 🧪 Ejecutar las Pruebas
Para ejecutar la suite de pruebas automatizadas, utiliza `pytest` desde la raíz del proyecto.
```bash
pytest
```

## 🧰 Scripts Utilitarios
El proyecto incluye scripts adicionales en la raíz para mantenimiento:

* **sync_to_chroma.py**: Lee todos los recursos de la base de datos SQLite y sincroniza sus embeddings con la base de datos vectorial ChromaDB. Es útil si necesitas reconstruir el índice de búsqueda.

* **check_cids.py**: Verifica el estado de todos los CIDs de IPFS almacenados en la base de datos para encontrar enlaces rotos o no disponibles.

## 📂 Estructura del Proyecto
```bash
.
├── app/                  # Directorio principal de la aplicación Flask
│   ├── routes/           # Blueprints para las rutas
│   │   ├── auth.py
│   │   ├── main.py
│   │   └── resources.py
│   ├── static/           # Archivos estáticos (JS, CSS, imágenes)
│   ├── templates/        # Plantillas HTML de Jinja2
│   ├── __init__.py       # Factory de la aplicación y configuración de SocketIO
│   ├── ipfs_client.py    # Cliente para interactuar con Web3.Storage
│   ├── models.py         # Modelo de datos de Usuario
│   ├── nlp_utils.py      # Funciones para generar embeddings y clasificar texto
│   └── vector_db.py      # Lógica para interactuar con ChromaDB
│
├── tests/                # Pruebas automatizadas
│   ├── conftest.py       # Fixtures de Pytest
│   └── test_app.py       # Pruebas de la aplicación
│
├── .env                  # (Debes crearlo) Variables de entorno
├── .gitignore
├── check_cids.py         # Script para verificar CIDs de IPFS
├── init_db.py            # Script para crear la base de datos
├── readme.md             # Este archivo
├── requirements.txt      # Dependencias de Python
├── run.py                # Punto de entrada para ejecutar la aplicación
└── sync_to_chroma.py     # Script para sincronizar con ChromaDB
```