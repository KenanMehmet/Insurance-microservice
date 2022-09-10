FROM tiangolo/meinheld-gunicorn-flask:python3.8

RUN set -ex \
    && apt-get update \
    && apt-get install -y wget unzip xvfb firefox-esr \
    && wget -O geckodriver.tar.gz https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz \
    && tar -xvzf geckodriver.tar.gz \
    && ls \
    && mv geckodriver /usr/bin/geckodriver \
    && chown root:root /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app
