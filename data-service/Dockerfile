FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN mkdir -p /data
VOLUME ["/data"]
EXPOSE 8002
CMD ["sh", "-c", "python app.py"]