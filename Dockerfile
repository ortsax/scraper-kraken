FROM python:3.14-slim AS builder

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /Orsta.py

RUN git clone https://github.com/realastrox11/Orsta.py .

RUN uv sync --frozen --no-cache

FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /Orsta.py

COPY --from=builder /Orsta.py .

ENV PATH="/Orsta.py/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uv", "run", "python", "main.py"]