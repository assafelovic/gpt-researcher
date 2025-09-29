###############################################
# 1) Dependencies layer
###############################################
FROM node:18.17.0-alpine AS deps
WORKDIR /app

# Copy only package manifest first for better layer caching
COPY package.json ./

# Install dependencies (no lock file present – recommend adding one for reproducibility)
RUN npm install --legacy-peer-deps

###############################################
# 2) Builder layer – builds Next.js (.next)
###############################################
FROM node:18.17.0-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build Next.js application (produces .next)
RUN npm run build \
	&& npm prune --production

###############################################
# 3) Runner layer – production image serving Next.js
###############################################
FROM node:18.17.0-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Copy only what is required at runtime
COPY --from=builder /app/package.json ./
COPY --from=builder /app/next.config.mjs ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

# Expose port (Next.js default)
EXPOSE 3000

# Start the Next.js production server (serves API routes too)
CMD ["npm", "run", "start"]

# Notes:
# - We moved away from the Nginx static approach because the app defines API Route Handlers
#   (e.g. files in app/api/*) which require the Next.js Node runtime.
# - If you later decide to produce a fully static export (`next export`), you can reintroduce
#   an Nginx (or any static) server, but dynamic API routes would no longer work.
