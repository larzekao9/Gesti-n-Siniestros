# Stage 1: base — imagen común con dependencias del SO
FROM node:20-alpine AS base
RUN apk add --no-cache libc6-compat curl
WORKDIR /app

# ─────────────────────────────────────────────────────────────
# Stage 2: deps — instala dependencias npm (aprovecha cache)
FROM base AS deps

COPY package.json package-lock.json* ./
# npm ci garantiza reproducibilidad exacta desde el lockfile
RUN npm ci

# ─────────────────────────────────────────────────────────────
# Stage 3: builder — compila la aplicación Next.js
FROM base AS builder

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Deshabilitar telemetría en build
ENV NEXT_TELEMETRY_DISABLED=1

# next.config.mjs debe tener output: 'standalone' para el runtime minimo
RUN npm run build

# ─────────────────────────────────────────────────────────────
# Stage 4: runner — imagen de producción mínima
FROM base AS runner

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Usuario no-root con UID/GID explícitos
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copiar artefactos públicos
COPY --from=builder /app/public ./public

# Copiar output standalone (incluye server.js y dependencias minimas)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER 1001

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
