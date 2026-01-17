FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tornado_file.py .
COPY styles ./styles
COPY templates ./templates

EXPOSE 8888
CMD ["python3","tornado_file.py"]
