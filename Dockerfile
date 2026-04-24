FROM python:3.12-slim

ARG VERSION=0.1.1

LABEL org.opencontainers.image.title="dpawb MCP Server"
LABEL org.opencontainers.image.description="Model Context Protocol server for the Digital Passport Model Assessment Workbench."
LABEL org.opencontainers.image.source="https://github.com/CE-RISE-software/dp-assessment-workbench"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL io.modelcontextprotocol.server.name="io.github.CE-RISE-software/dpawb"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md setup.py /app/
COPY src /app/src

RUN python -m pip install --no-cache-dir .

ENTRYPOINT ["dpawb-mcp"]
