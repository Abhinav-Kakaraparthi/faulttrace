# No runtime secret is referenced as a build argument or copied from the host.
FROM node:22.22.0-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
COPY fixtures/ /build/fixtures/
ENV VITE_FAULTTRACE_PROFILE=demo
RUN npm run build

FROM python:3.12.12-slim-bookworm AS application
ARG FAULTTRACE_BUILD_REVISION
ENV FAULTTRACE_BUILD_REVISION=${FAULTTRACE_BUILD_REVISION}
RUN python -c "import os,re; assert re.fullmatch('[0-9a-f]{40}', os.environ['FAULTTRACE_BUILD_REVISION']), 'exact_build_revision_required'"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FAULTTRACE_FRONTEND_DIST=/app/frontend/dist
WORKDIR /app
COPY requirements-backend.txt ./
RUN pip install --no-cache-dir -r requirements-backend.txt && pip check \
    && groupadd --gid 10001 faulttrace && useradd --uid 10001 --gid 10001 --no-create-home faulttrace \
    && mkdir /var/lib/faulttrace && chown faulttrace:faulttrace /var/lib/faulttrace
COPY faulttrace/ ./faulttrace/
COPY tools/start_public_demo.py ./tools/start_public_demo.py
COPY fixtures/ ./fixtures/
COPY --from=frontend /build/frontend/dist ./frontend/dist/
EXPOSE 10000
# Launcher fixes only the mounted directory owner, then drops to UID/GID 10001
# before opening any application data, accepting requests or reading provider keys.
CMD ["python", "tools/start_public_demo.py"]
