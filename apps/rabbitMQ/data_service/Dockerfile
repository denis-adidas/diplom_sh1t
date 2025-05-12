FROM python:3.11-slim

WORKDIR /data_service

COPY . .

RUN pip install --no-cache-dir -r requirements.txt


CMD ["python", "main.py"]