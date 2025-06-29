FROM python:3.14-rc-alpine3.21

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../pylib /app/pylib
COPY . /app/master-node

ENV PYTHONPATH="/app:/app/pylib"

CMD ["python", "master-node/main.py"]