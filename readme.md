# Plataforma REA - Recursos Educativos Abiertos

## Descripción
Esta es una plataforma web para la gestión de Recursos Educativos Abiertos (REA). Permite a los usuarios subir y gestionar recursos de aprendizaje, que son clasificados automáticamente usando modelos de Procesamiento de Lenguaje Natural (NLP) y almacenados de forma descentralizada en la red IPFS. La plataforma también incluye una funcionalidad de búsqueda semántica y una sala de comunicación P2P usando WebRTC.

## Características
* **Gestión de Recursos:** Añade nuevos recursos con título, descripción, categoría, enlace y/o archivo.
* **Almacenamiento en IPFS:** Los archivos adjuntos se suben a IPFS (InterPlanetary File System) usando la API de Web3.Storage, lo que garantiza su permanencia.
* **Clasificación Automática:** Utiliza un modelo de clasificación **zero-shot** para asignar automáticamente una categoría a cada recurso (por ejemplo, "programación", "matemáticas", "historia").
* **Búsqueda Semántica:** Los recursos son vectorizados usando embeddings de un modelo de lenguaje. La búsqueda utiliza similitud de coseno para encontrar los recursos más relevantes a una consulta, sin necesidad de coincidencia exacta de palabras clave.
* **WebRTC:** Incluye una sala P2P para chat y transferencia de archivos entre usuarios.

## Dependencias
El proyecto está construido sobre el framework Flask y requiere las siguientes librerías de Python.

## Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
    cd tu-repositorio
    ```

2.  **Crear y activar un entorno virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```

3.  **Instalar las dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar las variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables.
    * `SECRET_KEY`: Una cadena de texto para la clave secreta de Flask.
    * `WEB3_STORAGE_TOKEN`: Tu token de API para Web3.Storage.

5.  **Inicializar la base de datos:**
    ```bash
    python init_db.py
    ```

6.  **Ejecutar la aplicación:**
    ```bash
    python app.py
    ```
    La aplicación se ejecutará en `http://127.0.0.1:5000`.

## Uso
* **Página Principal:** Accede a `/` para la página de inicio.
* **Agregar Recurso:** Navega a `/nuevo` para añadir un nuevo recurso.
* **Ver Recursos:** Visita `/recursos` para ver la lista completa de recursos guardados.
* **Búsqueda Semántica:** Usa la página `/buscar_semantico` para realizar búsquedas basadas en la similitud semántica.
* **Sala WebRTC:** Accede a `/webrtc` para probar la funcionalidad P2P.