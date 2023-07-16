FROM python:3.11.4

RUN apt-get update
RUN apt-get install -y fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libgtk-4-1 libnspr4 libnss3 libu2f-udev libvulkan1 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 xdg-utils

# Install broswer
RUN apt update
RUN wget https://dl.google.com/linux/deb/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.198-1_amd64.deb
RUN apt install wget
RUN dpkg -i google-chrome-stable_114.0.5735.198-1_amd64.deb
RUN apt-get install -f
RUN google-chrome --version

# Install chrome driver
RUN wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY ./ ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

