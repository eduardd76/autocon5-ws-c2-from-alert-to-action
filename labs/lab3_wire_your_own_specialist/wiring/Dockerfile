# Lab 3 wire-in: runner for YOUR specialist.
# Build context is ./services (so it can COPY shared/), like the other agents.
FROM python:3.11-slim
WORKDIR /app
COPY your-agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY your-agent/main.py /app/
CMD ["python", "main.py"]
