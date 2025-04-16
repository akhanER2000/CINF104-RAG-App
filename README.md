# Asistente RAG para Materiales del Curso CINF104

Este proyecto implementa un asistente conversacional basado en la arquitectura RAG (Retrieval-Augmented Generation) para realizar consultas en lenguaje natural sobre los materiales del curso "CINF104 - Aprendizaje de Máquina". La aplicación permite cargar documentos PDF del curso, procesarlos y luego responder preguntas utilizando modelos de lenguaje grandes (LLMs) locales servidos a través de Ollama, todo ello orquestado mediante Docker.

Este proyecto fue desarrollado como parte de una evaluación del curso CINF104.

## Tecnologías Utilizadas

* **Python:** Lenguaje principal de programación.
* **Streamlit:** Framework para construir la interfaz de usuario web interactiva.
* **Langchain:** Framework para construir la lógica RAG (carga de documentos, división, embeddings, recuperación, prompts y cadenas).
* **Ollama:** Herramienta para servir y ejecutar modelos LLM localmente. Se ejecuta en un contenedor Docker.
* **ChromaDB:** Base de datos vectorial para almacenar y buscar los embeddings de los documentos. Persiste los datos en una carpeta local mapeada.
* **FastEmbed:** Biblioteca para generar los embeddings de texto de forma eficiente localmente.
* **Docker & Docker Compose:** Para contenerizar la aplicación y sus dependencias (Ollama y la app Streamlit/RAG), asegurando un entorno de ejecución consistente.
* **PyPDF:** Biblioteca para cargar el contenido de los archivos PDF.

## Características

* Interfaz de chat simple e intuitiva construida con Streamlit.
* Procesamiento e indexación de documentos PDF ubicados en una carpeta local (`docs/`).
* Almacenamiento persistente de la base de datos vectorial en una carpeta local (`chroma_db/`).
* Generación de respuestas aumentada por recuperación (RAG), utilizando el contenido de los PDFs como contexto.
* Selección dinámica del modelo LLM (servido por Ollama) a través de la interfaz de usuario.
* Configuración de la temperatura del LLM para ajustar la creatividad/factualidad de las respuestas.
* Ejecución completa utilizando contenedores Docker, facilitando la portabilidad y el despliegue.

## Prerrequisitos

Antes de empezar, asegúrate de tener instalado:

1.  **Docker Desktop:** Necesario para construir y ejecutar los contenedores definidos en `docker-compose.yml`. Descárgalo desde [docker.com](https://www.docker.com/products/docker-desktop/).
2.  **Ollama (CLI Local):** Necesitas la interfaz de línea de comandos (`ollama`) instalada localmente para descargar los modelos LLM fácilmente *a través del contenedor en ejecución* (ver paso de configuración). Descárgala desde [ollama.ai](https://ollama.ai/).
3.  **Git:** Para clonar este repositorio.

## Instalación y Configuración

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/akhanER2000/CINF104-RAG-App.git
    cd CINF104-RAG-App 
    ```

2.  **Añadir Documentos PDF:**
    * Copia todos los archivos PDF del curso CINF104 (sílabo, presentaciones, etc.) que deseas consultar dentro de la carpeta `docs/`.

3.  **Iniciar Contenedores (Paso Previo a Descargar Modelos):**
    * Abre una terminal en la carpeta raíz del proyecto.
    * Ejecuta `docker-compose up -d` para iniciar los servicios Ollama y la App en segundo plano. Espera un momento a que se inicien.
    ```bash
    docker-compose up -d 
    ```

4.  **Descargar Modelos LLM con Ollama (Método Correcto):**
    * **Importante:** Usa `docker exec` para descargar los modelos *directamente dentro* del contenedor Ollama en ejecución. Esto asegura que se guarden en el volumen correcto.
    * Abre *otra* terminal (o usa la misma después del `up -d`) y ejecuta (ajusta los nombres si usaste otros):
        ```bash
        docker exec -it ollama_service ollama pull llama3:8b
        docker exec -it ollama_service ollama pull mistral:latest
        # Añade aquí otros modelos si es necesario (ej. phi3)
        docker exec -it ollama_service ollama pull phi 
        ```
    * Espera a que cada descarga termine.
    * **Verifica** que los modelos están listados dentro del contenedor:
        ```bash
        docker exec -it ollama_service ollama list
        ```

## Ejecución (Si los contenedores no están corriendo)

1.  **Construir e Iniciar Contenedores:**
    * Asegúrate de que Docker Desktop esté corriendo.
    * Abre una terminal en la carpeta raíz del proyecto (`CINF104-RAG-App/`).
    * Ejecuta el comando:
        ```bash
        docker-compose up --build
        ```
    * `--build`: Reconstruye la imagen de la aplicación si has hecho cambios.
    * Espera a que ambos contenedores se inicien correctamente. Verás los logs en la terminal. Si usaste `up -d` antes, los contenedores ya deberían estar corriendo.

## Uso de la Aplicación

1.  **Acceder a la Interfaz:** Abre tu navegador web y ve a `http://localhost:8501`.
2.  **Indexar Documentos:**
    * En la barra lateral izquierda, haz clic en el botón **"Procesar e Indexar Documentos"**.
    * Espera a que el proceso termine (verás mensajes de estado y un mensaje de éxito). Este paso solo necesitas hacerlo la primera vez o si añades/cambias PDFs en la carpeta `docs/`.
3.  **Seleccionar Modelo:** En la barra lateral, elige el modelo LLM que deseas usar para tus consultas (ej. `llama3:8b`, `mistral:latest`). Puedes ajustar la temperatura también.
4.  **Chatear:** Escribe tus preguntas sobre el contenido de los documentos del curso en la caja de chat inferior y presiona Enter.

## Detener la Aplicación

1.  Ve a la terminal donde ejecutaste `docker-compose up` (si no usaste `-d`) y presiona `Ctrl+C`.
2.  Para detener y eliminar los contenedores (pero mantener los volúmenes con los modelos y la BD vectorial), ejecuta en la terminal del proyecto:
    ```bash
    docker-compose down
    ```

## Solución de Problemas Comunes

Durante la configuración y ejecución, podrías encontrar algunos de los siguientes errores que ya fueron resueltos durante el desarrollo de este proyecto:

### 1. Error: `yaml: invalid trailing UTF-8 octet`

* **Síntoma:** Ocurre al ejecutar `docker-compose up`.
* **Causa:** El archivo `docker-compose.yml` no está guardado con la codificación correcta (UTF-8) o contiene caracteres inválidos.
* **Solución:**
    1.  Abre `docker-compose.yml` en tu editor (VS 2022, VS Code, etc.).
    2.  Usa la opción "Guardar con codificación" (Save with Encoding).
    3.  Selecciona explícitamente **`UTF-8`** (asegúrate que NO sea "UTF-8 with BOM").
    4.  Guarda el archivo.
    5.  Si persiste, recrea el archivo: copia el contenido correcto, borra el archivo original, crea uno nuevo asegurando que sea UTF-8, pega el contenido y guarda.

### 2. Error: `UnicodeDecodeError: 'utf-8' codec can't decode byte ...` (durante el build)

* **Síntoma:** Ocurre durante el paso `pip install -r requirements.txt` al ejecutar `docker-compose up --build`.
* **Causa:** El archivo `requirements.txt` no está guardado con codificación UTF-8 o contiene caracteres inválidos.
* **Solución:** Aplica la misma solución que para el error anterior, pero esta vez sobre el archivo `requirements.txt`. Asegúrate de guardarlo como **UTF-8 (sin BOM)**.

### 3. Error: `Ollama call failed with status code 404. Maybe your model is not found...`

* **Síntoma:** Ocurre en la aplicación Streamlit al intentar hacer una consulta, después de indexar los documentos.
* **Causa:** El servicio Ollama dentro del contenedor Docker no encuentra el modelo LLM solicitado (ej. `llama3:8b`). Esto suele pasar porque los modelos descargados con `ollama pull` en el *host* no están en el volumen que usa el contenedor (`ollama_data`).
* **Solución:** Descarga los modelos *a través del contenedor Ollama* una vez que esté corriendo (ver sección "Instalación y Configuración", paso 4). Usa `docker exec -it ollama_service ollama pull <nombre_modelo>` y verifica con `docker exec -it ollama_service ollama list`.

## Estructura del Proyecto
CINF104-RAG-App/
├── docs/               # Carpeta para los archivos PDF del curso
├── chroma_db/          # Carpeta donde ChromaDB guarda la base de datos vectorial
├── .venv/              # (Opcional) Entorno virtual Python local
├── app.py              # Script principal de la aplicación Streamlit y lógica RAG
├── requirements.txt    # Dependencias Python
├── Dockerfile          # Instrucciones para construir la imagen Docker de la app
├── docker-compose.yml  # Define y orquesta los servicios Docker (app y Ollama)
├── README.md           # Este archivo
└── .gitignore          # Especifica archivos/carpetas a ignorar por Git

## Notas Adicionales

* **GPU:** Si tienes una GPU Nvidia compatible y Docker configurado para usarla, puedes descomentar la sección `deploy` en el servicio `ollama` dentro de `docker-compose.yml` para obtener respuestas más rápidas del LLM.
* **Encoding:** Asegúrate de que todos los archivos de texto (`.py`, `.txt`, `.yml`, `.md`) estén guardados con codificación UTF-8 para evitar errores.
