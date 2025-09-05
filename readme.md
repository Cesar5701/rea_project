# 🚀 Plataforma REA - Recursos Educativos Abiertos

## Descripción
Esta es una plataforma web para la gestión de **Recursos Educativos Abiertos (REA)**. Permite a los usuarios registrarse, iniciar sesión, y compartir recursos de aprendizaje. Los recursos son clasificados automáticamente usando modelos de Procesamiento de Lenguaje Natural (NLP) y los archivos se almacenan de forma descentralizada en la red IPFS.

La plataforma también incluye una potente funcionalidad de **búsqueda semántica** y una **sala de comunicación P2P** en tiempo real usando WebRTC.

## ✨ Características Principales
* **Autenticación de Usuarios:** Sistema completo de registro, inicio de sesión y gestión de sesiones.
* **Gestión de Recursos:** Añade, visualiza y gestiona recursos con título, descripción, categoría, enlace y/o archivo.
* **Almacenamiento Descentralizado en IPFS:** Los archivos se suben a IPFS (InterPlanetary File System) usando la API de Web3.Storage, garantizando su persistencia y descentralización.
* **Clasificación Automática con IA:** Utiliza un modelo de clasificación **zero-shot** (Hugging Face Transformers) para asignar automáticamente una categoría a cada recurso (p. ej., "programación", "matemáticas", "historia").
* **Búsqueda Semántica:** Los recursos son vectorizados usando *embeddings*. La búsqueda utiliza similitud de coseno para encontrar los recursos más relevantes, entendiendo el significado de la consulta, no solo las palabras clave.
* **Sala de Colaboración P2P:** Incluye una sala de chat y transferencia de archivos en tiempo real entre usuarios usando **WebRTC** y WebSockets.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Flask, Flask-Login, Flask-SocketIO
* **Base de Datos:** SQLite
* **NLP:** Transformers (Hugging Face), PyTorch, Numpy
* **Frontend:** HTML, Tailwind CSS, JavaScript
* **Almacenamiento:** IPFS (via Web3.Storage)
* **Comunicación en tiempo real:** WebRTC, Socket.IO

## ⚙️ Instalación

Sigue estos pasos para poner en marcha el proyecto en tu entorno local.

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
    cd tu-repositorio
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
    > **Nota:** Este comando descargará las librerías de PyTorch y Transformers, que incluyen modelos de lenguaje de varios cientos de megabytes. La primera vez puede tardar un poco.

4.  **Configurar las variables de entorno:**
    Crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables:
    ```ini
    # Clave secreta para proteger las sesiones de Flask. Puedes poner cualquier cadena segura.
    SECRET_KEY='una-clave-muy-segura-y-dificil-de-adivinar'

    # Tu token de API de Web3.Storage para poder subir archivos a IPFS.
    WEB3_STORAGE_TOKEN='TU_API_TOKEN_DE_WEB3_STORAGE'
    ```

5.  **Inicializar la base de datos:**
    Ejecuta este script una sola vez para crear el archivo `rea.db` y las tablas necesarias.
    ```bash
    python init_db.py
    ```

## ▶️ Ejecución

1.  **Iniciar la aplicación:**
    ```bash
    python app.py
    ```
2.  La aplicación se ejecutará en modo de depuración en `http://127.0.0.1:5000`.
    > **Importante:** La primera vez que inicies la aplicación, el script `nlp_utils.py` descargará los modelos de Hugging Face. Este proceso puede tardar varios minutos dependiendo de tu conexión a internet. Las siguientes veces que inicies la app será instantáneo.

## 📂 Estructura del Proyecto