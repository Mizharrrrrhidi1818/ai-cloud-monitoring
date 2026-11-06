
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY dashboards/ ./dashboards/

EXPOSE 8501

CMD ["python", "-m", "streamlit", "run", "dashboards/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]
