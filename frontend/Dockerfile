FROM node:20-alpine
RUN apk add --no-cache curl
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npx", "vite", "preview", "--port", "3000", "--host", "0.0.0.0"]
