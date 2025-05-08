FROM node:18.17.0-alpine as builder
ARG TARGETPLATFORM
WORKDIR /app
COPY ./package.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN if [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
      export NEXT_DISABLE_SWC=1; \
    fi && \
    export NEXT_IGNORE_ESLINT=true && \
    npm run build

FROM nginx
EXPOSE 3000
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /usr/share/nginx/html
