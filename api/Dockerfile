FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hacer el entrypoint ejecutable
RUN chmod +x entrypoint.sh

# Usar bash para el entrypoint
CMD ["bash", "entrypoint.sh"]
