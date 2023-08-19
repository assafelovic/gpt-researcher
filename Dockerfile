# Usar la imagen base de Python
FROM python:3.11.4-slim-bullseye as install-browser

# Actualizar e instalar dependencias necesarias
RUN apt-get update && apt-get install -y wget unzip
# Instalar las dependencias necesarias para WeasyPrint
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info

# Descargar Chrome desde la URL específica
RUN wget https://www.slimjet.com/chrome/download-chrome.php?file=files%2F104.0.5112.102%2Fgoogle-chrome-stable_current_amd64.deb -O chrome.deb

# Intentar instalar Chrome
RUN dpkg -i chrome.deb 

# Resolver dependencias
RUN apt-get -f install -y

# Eliminar el archivo .deb de Chrome
RUN rm chrome.deb

# Descargar e instalar ChromeDriver desde la URL específica
RUN wget https://chromedriver.storage.googleapis.com/104.0.5112.79/chromedriver_linux64.zip -O chromedriver.zip \
    && unzip chromedriver.zip \
    && mv chromedriver /usr/bin/chromedriver \
    && chown root:root /usr/bin/chromedriver \
    && chmod +x /usr/bin/chromedriver

# Configurar el entorno de trabajo
FROM install-browser as gpt-researcher-install

ENV PIP_ROOT_USER_ACTION=ignore

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Copiar y instalar las dependencias
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Configurar el usuario y permisos
FROM gpt-researcher-install AS gpt-researcher

RUN useradd -ms /bin/bash gpt-researcher \
    && chown -R gpt-researcher:gpt-researcher /usr/src/app

USER gpt-researcher

# Copiar el resto de los archivos y configurar el comando de inicio
COPY ./ ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


