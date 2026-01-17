FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com && npm install

COPY . .

CMD ["npm", "run", "dev"]
