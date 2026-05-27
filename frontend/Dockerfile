FROM node:20-alpine

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --include=dev

COPY frontend/src /app/src
COPY frontend/next-env.d.ts /app/next-env.d.ts
COPY frontend/next.config.ts /app/next.config.ts
COPY frontend/postcss.config.mjs /app/postcss.config.mjs
COPY frontend/tsconfig.json /app/tsconfig.json
RUN npm run build

ENV NODE_ENV=production

EXPOSE 3000

CMD ["npm", "run", "start"]
