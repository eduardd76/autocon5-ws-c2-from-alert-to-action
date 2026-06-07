FROM python:3.11-slim
WORKDIR /app
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY mcp-server/main.py .
EXPOSE 8000
CMD ["python", "main.py"]
