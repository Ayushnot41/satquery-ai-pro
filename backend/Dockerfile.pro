FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace/backend
COPY backend/requirements-core.txt ./requirements-core.txt
COPY backend/requirements-lock.txt ./requirements-lock.txt
RUN pip install --no-cache-dir -r requirements-core.txt -c requirements-lock.txt && useradd --create-home --uid 10001 satquery
COPY backend/app ./app
COPY assets /workspace/assets
COPY index.html bhuvision_preview.html manifest.json /workspace/
COPY legacy /workspace/legacy
COPY docs /workspace/docs
RUN mkdir -p data/uploads data/demo && chown -R satquery:satquery /workspace
USER satquery
EXPOSE 8010
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/api/health/ready',timeout=3)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8010", "--no-proxy-headers"]
