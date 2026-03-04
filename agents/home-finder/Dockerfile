FROM python:3.12-slim
WORKDIR /app

COPY shared/ /shared/
RUN pip install --no-cache-dir /shared/

COPY agents/home-finder/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agents/home-finder/app/ ./app/

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
