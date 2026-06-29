FROM node:20-slim AS build

WORKDIR /app

# Copy package files from the root context
COPY package*.json ./
COPY apps/frontend/package*.json ./apps/frontend/

RUN rm -rf package-lock.json
RUN npm install

# Copy everything
COPY . .

# Build the frontend
WORKDIR /app/apps/frontend
RUN npx vite build

# Use nginx to serve the static content
FROM nginx:stable-alpine
COPY --from=build /app/apps/frontend/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
