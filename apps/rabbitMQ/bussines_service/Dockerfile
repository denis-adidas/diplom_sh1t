FROM python:3.11-slim

WORKDIR /bussines_service

COPY . .

RUN pip install --no-cache-dir -r requirements.txt


COPY . .

CMD ["python", "main.py"]