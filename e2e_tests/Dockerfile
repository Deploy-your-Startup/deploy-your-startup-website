FROM node:24-bookworm-slim
WORKDIR /workspace/e2e_tests
COPY e2e_tests/package*.json ./
RUN npm ci && npx playwright install --with-deps --only-shell chromium \
 && rm -rf /var/lib/apt/lists/* /root/.npm/_cacache
WORKDIR /workspace/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
WORKDIR /workspace/e2e_tests
COPY e2e_tests/ ./
CMD ["./make.sh", "ci_e2e"]
