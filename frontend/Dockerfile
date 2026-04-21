# ── Development stage ─────────────────────────────────────────────────────
FROM node:22-alpine AS dev

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || pnpm install

COPY . .

EXPOSE 8080

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "8080"]

# ── Production build stage ───────────────────────────────────────────────
FROM node:22-alpine AS build

WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || pnpm install

COPY . .
RUN pnpm build

# ── Production serve stage ───────────────────────────────────────────────
FROM nginx:alpine AS prod

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
