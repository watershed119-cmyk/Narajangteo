FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY narajangteo ./narajangteo
RUN pip install --no-cache-dir .

CMD ["narajangteo"]
