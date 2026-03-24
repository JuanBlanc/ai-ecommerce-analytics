FROM node:20-alpine

WORKDIR /app

# Instalar dependencias primero (se cachea si package.json no cambia)
COPY package.json package-lock.json* ./
RUN npm install --prefer-offline --no-audit --progress=false

# Copiar código fuente
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
