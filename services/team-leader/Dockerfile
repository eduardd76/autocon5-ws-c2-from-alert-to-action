FROM python:3.11-slim
WORKDIR /app
COPY team-leader/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY team-leader/main.py /app/
EXPOSE 8002
CMD ["python", "main.py"]
