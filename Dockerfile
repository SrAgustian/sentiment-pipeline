FROM apache/airflow:2.9.1

USER root

# Install dependencies sistem dan Google Chrome
RUN apt-get update && apt-get install -y wget unzip gnupg2 \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy dan install requirements.txt 
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt