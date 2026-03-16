# =============================================================================
# Stage 1: 依存関係のインストール
# =============================================================================
FROM node:24-slim AS deps

RUN corepack enable && corepack prepare pnpm@10.24.0 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# =============================================================================
# Stage 2: Next.js ビルド
# =============================================================================
FROM node:24-slim AS builder

RUN corepack enable && corepack prepare pnpm@10.24.0 --activate

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_FULL_URL
ARG NEXT_PUBLIC_BACKEND_URL
ARG NEXT_PUBLIC_BASE_PATH

# Set ENV vars with bash defaults so they work even if ARG is empty string
ENV NEXT_PUBLIC_FULL_URL=${NEXT_PUBLIC_FULL_URL:-http://localhost:3400/peak-sight}
ENV NEXT_PUBLIC_BACKEND_URL=${NEXT_PUBLIC_BACKEND_URL:-http://localhost:8200}
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH:-/peak-sight}

RUN pnpm build

# =============================================================================
# Stage 3: Production ランタイム
# =============================================================================
FROM node:24-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# standalone 出力をコピー
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

ARG PORT=3400
ENV PORT=${PORT}
ENV HOSTNAME=0.0.0.0

EXPOSE ${PORT}

CMD ["node", "server.js"]
