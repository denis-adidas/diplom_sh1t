FROM python:3.11-slim

WORKDIR /locust
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["locust", "-f", "locustfile.py", "--host=http://manage-service:8000"]
