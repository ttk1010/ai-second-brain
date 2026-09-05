# Lambda container image for AI Second Brain instant generation (Issue #42, ADR 0015).
# Build context is the repository root (see infra/template.yaml DockerContext).
# The function is arm64 (Graviton); the base image is multi-arch, so `sam build`
# on an arm64 host (Apple Silicon) produces an arm64 image natively. On an x86_64
# host, build with `--platform linux/arm64` to match the function architecture.
FROM public.ecr.aws/lambda/python:3.12

# Install runtime dependencies first for better layer caching.
COPY infra/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code onto the Lambda task root (already on sys.path).
COPY backend ${LAMBDA_TASK_ROOT}/backend

# Function URL invokes this handler (ADR 0015: sync generation).
CMD ["backend.cloud.handler.lambda_handler"]
