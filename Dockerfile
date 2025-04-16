# Usa una imagen base de Python espec�fica y ligera
FROM python:3.11-slim 

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero para aprovechar el cach� de Docker
COPY requirements.txt ./

# Instala las dependencias
# --no-cache-dir reduce el tama�o de la imagen
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia el resto del c�digo de la aplicaci�n al directorio de trabajo
# Esto incluye app.py y cualquier otro script o archivo que necesites
COPY . /app

# Expone el puerto est�ndar de Streamlit
EXPOSE 8501

# (Opcional pero recomendado) Chequeo de salud b�sico para Streamlit
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Comando para ejecutar la aplicaci�n Streamlit al iniciar el contenedor
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]