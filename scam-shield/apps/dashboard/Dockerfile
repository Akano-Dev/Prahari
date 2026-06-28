# Dashboard dev/preview image. For production, `npm run build` and serve dist/ via nginx.
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
