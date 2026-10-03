FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 HF_HOME=/app/pokedata/hf
RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pokescan.py app.py ./
COPY static static
EXPOSE 8085
CMD ["gunicorn", "-b", "0.0.0.0:8085", "-w", "1", "--threads", "2", "--timeout", "180", "app:app"]
