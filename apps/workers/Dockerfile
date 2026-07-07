FROM python:3.12-slim
WORKDIR /app
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api/app /app/app
COPY apps/workers/src /app/workers
CMD ["python", "-m", "workers.relayer"]
