# Usa una imagen base de Python específica y ligera
FROM python:3.11-slim 

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt ./

# Instala las dependencias
# --no-cache-dir reduce el tamaño de la imagen
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación al directorio de trabajo
# Esto incluye app.py y cualquier otro script o archivo que necesites
COPY . /app

# Expone el puerto estándar de Streamlit
EXPOSE 8501

# (Opcional pero recomendado) Chequeo de salud básico para Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando para ejecutar la aplicación Streamlit al iniciar el contenedor
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]