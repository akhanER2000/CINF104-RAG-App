import os
import glob
import streamlit as st
from streamlit_chat import message # Opcional, para un estilo de chat específico

# Importaciones de Langchain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings # Embeddings locales rápidos
from langchain_community.chat_models import ChatOllama # Para interactuar con Ollama
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# --- Configuración Inicial ---

# Cargar variables de entorno o usar valores por defecto (definidos en docker-compose.yml)
DOCS_PATH = os.getenv("DOCS_PATH", "docs")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") # Asegúrate que coincida con docker-compose

# Modelos disponibles en Ollama (asegúrate de tenerlos descargados: ollama pull mistral, ollama pull llama3, etc.)
AVAILABLE_MODELS = ["mistral", "llama3", "phi", "llama3:8b","mistral:latest" ] # Añade los modelos que quieras probar

# Nombre del modelo para FastEmbed (puedes cambiarlo si prefieres otro)
# 'BAAI/bge-small-en-v1.5' es una opción popular y eficiente
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# --- Funciones Principales ---

# Cargar modelo de embeddings (cacheado por Streamlit para eficiencia)
@st.cache_resource
def load_embedding_model():
    """Carga el modelo FastEmbed."""
    try:
        return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    except Exception as e:
        st.error(f"Error al cargar el modelo de embeddings ({EMBEDDING_MODEL_NAME}): {e}")
        return None

# Procesar e indexar documentos PDF
def process_and_ingest_documents():
    """
    Carga PDFs desde DOCS_PATH, los divide en chunks, 
    genera embeddings y los almacena en ChromaDB.
    Retorna True si fue exitoso, False en caso contrario.
    """
    pdf_files = glob.glob(os.path.join(DOCS_PATH, "*.pdf"))
    if not pdf_files:
        st.error(f"No se encontraron archivos PDF en la carpeta '{DOCS_PATH}'. Por favor, añade documentos.")
        return False

    docs_list = []
    st.info(f"Encontrados {len(pdf_files)} PDF(s) en '{DOCS_PATH}'. Cargando...")
    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(pdf_file)
            docs_list.extend(loader.load()) # Carga y combina documentos de todos los PDFs
        except Exception as e:
            st.error(f"Error cargando '{os.path.basename(pdf_file)}': {e}")
            # Continúa con otros archivos si uno falla
    
    if not docs_list:
        st.error("No se pudo cargar ningún documento PDF.")
        return False

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # Tamaño de los chunks
        chunk_overlap=200, # Solapamiento entre chunks
        length_function=len
    )
    chunks = text_splitter.split_documents(docs_list)
    st.info(f"Se dividieron {len(docs_list)} páginas/documentos en {len(chunks)} chunks.")

    if not chunks:
        st.error("Fallo al dividir los documentos en chunks.")
        return False

    st.info("Inicializando modelo de embeddings...")
    embedding_model = load_embedding_model()
    if embedding_model is None:
         return False # Error ya mostrado en load_embedding_model

    st.info(f"Creando/actualizando la base de datos vectorial en '{CHROMA_PERSIST_DIR}'...")
    try:
        # Asegura que el directorio exista
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True) 
        
        # Crea o reemplaza la base de datos Chroma con los nuevos chunks
        vector_store = Chroma.from_documents(
            documents=chunks, 
            embedding=embedding_model,
            persist_directory=CHROMA_PERSIST_DIR # Guarda la BD en la carpeta especificada
        )
        st.success(f"¡Documentos procesados y almacenados exitosamente en '{CHROMA_PERSIST_DIR}'!")
        return True
    except Exception as e:
        st.error(f"Error al crear/actualizar la base de datos vectorial: {e}")
        return False

# Cargar la base de datos Chroma existente
def load_vector_store():
    """Carga la base de datos ChromaDB persistida."""
    embedding_model = load_embedding_model()
    if embedding_model is None:
        return None # Error ya mostrado

    if not os.path.exists(CHROMA_PERSIST_DIR) or not os.listdir(CHROMA_PERSIST_DIR):
         st.warning(f"Base de datos vectorial no encontrada en '{CHROMA_PERSIST_DIR}'. Por favor, procesa los documentos primero.")
         return None
    try:
        return Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embedding_model)
    except Exception as e:
        st.error(f"Error al cargar la base de datos vectorial desde '{CHROMA_PERSIST_DIR}': {e}")
        return None

# --- Interfaz de Usuario Streamlit ---

st.set_page_config(page_title="Asistente CINF104", layout="wide")
st.title("🤖 Asistente de Consulta para Materiales CINF104")
st.markdown(f"Realiza preguntas sobre los documentos PDF encontrados en la carpeta `{DOCS_PATH}`.")

# --- Sidebar para Configuración y Acciones ---
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Selector de modelo LLM
    selected_model = st.selectbox("Selecciona el modelo LLM:", AVAILABLE_MODELS, index=0) # 'mistral' por defecto si está en la lista
    
    # Control de Temperatura (creatividad vs factualidad)
    temperature = st.slider("Temperatura del LLM:", min_value=0.0, max_value=1.0, value=0.2, step=0.1)

    st.divider()
    st.header("📚 Gestión de Documentos")
    st.markdown(f"Directorio de documentos: `{DOCS_PATH}`")
    st.markdown(f"Base de datos vectorial: `{CHROMA_PERSIST_DIR}`")
    
    # Botón para iniciar la ingesta
    if st.button("Procesar e Indexar Documentos"):
        with st.spinner("Procesando documentos... Esto puede tardar unos minutos."):
            success = process_and_ingest_documents()
            if success:
                # Forza la recarga del vector store en el estado de sesión después de la ingesta
                st.session_state['vector_store'] = load_vector_store() 
            else:
                st.session_state['vector_store'] = None # Asegura que es None si falla

# --- Lógica Principal del Chat ---

# Cargar el vector store una vez y guardarlo en el estado de sesión
if 'vector_store' not in st.session_state:
    st.session_state['vector_store'] = load_vector_store()

# Inicializar historial de chat si no existe
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": f"Hola! Listo para responder preguntas sobre los documentos en '{DOCS_PATH}'. Selecciona un modelo y haz tu pregunta."}]

# Mostrar mensajes del historial
for msg in st.session_state.messages:
    # Usar st.chat_message que es nativo y más estándar
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input del usuario
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Añadir mensaje del usuario al historial y mostrarlo
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Obtener el vector store del estado de sesión
    vector_store = st.session_state.get('vector_store')

    # Verificar si el vector store está cargado
    if vector_store is None:
        st.warning("La base de datos de documentos no está cargada. Por favor, usa el botón 'Procesar e Indexar Documentos' en la barra lateral.")
        st.session_state.messages.append({"role": "assistant", "content": "Error: No se pudo acceder a la base de datos de documentos."})
        # Refrescar la UI para mostrar el warning
        st.rerun() 
    else:
        # Si el vector store está listo, proceder con RAG
        with st.chat_message("assistant"):
            message_placeholder = st.empty() # Placeholder para la respuesta
            with st.spinner(f"Pensando con el modelo {selected_model}..."):
                try:
                    # 1. Inicializar LLM seleccionado por el usuario
                    llm = ChatOllama(model=selected_model, base_url=OLLAMA_BASE_URL, temperature=temperature)

                    # 2. Crear Retriever (busca en la BD vectorial)
                    retriever = vector_store.as_retriever(search_kwargs={'k': 5}) # Obtener los 5 chunks más relevantes

                    # 3. Definir el Prompt Template para RAG
                    RAG_PROMPT_TEMPLATE = """
                    CONTEXTO:
                    {context}

                    PREGUNTA:
                    {question}

                    INSTRUCCIONES:
                    Basándote SOLAMENTE en el CONTEXTO proporcionado arriba, responde la PREGUNTA de forma concisa y clara en español.
                    Si la respuesta no se encuentra explícitamente en el CONTEXTO, indica: "La información solicitada no se encuentra en los documentos proporcionados."
                    No inventes información ni utilices conocimiento externo. Si citas partes del contexto, hazlo brevemente.

                    RESPUESTA:"""
                    rag_prompt = PromptTemplate.from_template(RAG_PROMPT_TEMPLATE)

                    # 4. Definir la Cadena RAG usando LangChain Expression Language (LCEL)
                    def format_docs(docs):
                         # Formatea los documentos recuperados para el prompt
                         return "\n\n---\n\n".join(f"Fuente (Página {doc.metadata.get('page', '?')}):\n{doc.page_content}" for doc in docs)

                    rag_chain = (
                        {"context": retriever | format_docs, "question": RunnablePassthrough()} # Pasa la pregunta y el contexto formateado
                        | rag_prompt # Aplica el template
                        | llm        # Llama al LLM
                        | StrOutputParser() # Extrae la respuesta como texto
                    )

                    # 5. Invocar la cadena y obtener la respuesta
                    response = rag_chain.invoke(prompt)
                    
                    # Mostrar la respuesta en el placeholder
                    message_placeholder.markdown(response) 
                    
                    # Añadir respuesta del asistente al historial
                    st.session_state.messages.append({"role": "assistant", "content": response})

                except Exception as e:
                    error_msg = f"Ocurrió un error al procesar la pregunta con {selected_model}: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": f"Lo siento, {error_msg}"})