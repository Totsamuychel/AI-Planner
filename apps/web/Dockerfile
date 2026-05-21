FROM node:20-bookworm-slim

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1 \
    CI=1

RUN corepack enable && corepack prepare pnpm@9.12.0 --activate

COPY package.json ./
RUN pnpm install --no-frozen-lockfile

COPY . .

EXPOSE 3000
CMD ["pnpm", "dev"]
