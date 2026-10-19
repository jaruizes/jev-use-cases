# CPU-only HTTP inference service for Apple Silicon Docker Desktop (no MPS passthrough).
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 HF_HOME=/models/huggingface
RUN pip install --no-cache-dir "laya[serve]"
EXPOSE 8000
CMD ["laya-serve"]
