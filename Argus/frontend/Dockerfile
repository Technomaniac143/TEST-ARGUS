# Stage 1: Build Next.js application
FROM node:20-slim AS builder

WORKDIR /app

# Copy dependency configurations
COPY package*.json ./

# Install dependencies (including devDependencies needed for build)
RUN npm ci

# Copy frontend source files
COPY . .

# Declare and inject build-time API URL environment variable
ARG NEXT_PUBLIC_ARGUS_API_URL
ENV NEXT_PUBLIC_ARGUS_API_URL=$NEXT_PUBLIC_ARGUS_API_URL

# Build Next.js application
RUN npm run build

# Stage 2: Minimal production environment
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built app and required configurations from the builder stage
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Install only production dependencies to keep the image slim
RUN npm ci --omit=dev

# Expose port (Railway overrides this)
EXPOSE 3000

# Start Next.js server binding to the environment PORT
CMD ["sh", "-c", "npx next start -p ${PORT:-3000}"]
