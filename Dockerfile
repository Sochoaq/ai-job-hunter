# syntax=docker/dockerfile:1
# ==============================================================================
# Multi-Stage Dockerfile - AI Job Hunter (Python Orchestrator & Supply-Chain QA)
# ==============================================================================

# --- Stage 1: Builder (Installs Python dependencies into isolated venv) ---
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime (Hardened non-root image, zero personal artifacts) ---
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="AI Job Hunter Orchestrator" \
      org.opencontainers.image.description="Multi-agent LLM job evaluation, posting sanitization, and dual-engine PDF pipeline" \
      org.opencontainers.image.source="https://github.com/Sochoaq/ai-job-hunter" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --gid 10001 hunter && \
    useradd --uid 10001 --gid hunter --no-create-home --shell /usr/sbin/nologin hunter && \
    mkdir -p /app/output && \
    chown -R hunter:hunter /app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=hunter:hunter orchestrator.py job_scout.py job_tracker.py pdf_generator.py hunt.py run_batch.py salary_lookup.py candidate_config.example.json .gitignore README.md SETUP.md ./
COPY --chown=hunter:hunter assets ./assets
COPY --chown=hunter:hunter tools ./tools
COPY --chown=hunter:hunter tests ./tests
COPY --chown=hunter:hunter .claude ./.claude
COPY --chown=hunter:hunter .agents ./.agents

USER hunter

CMD ["python", "tools/security_guards.py"]
