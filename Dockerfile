# geo-score's MCP server (stdio) in a container: the two standard-library CLI files and nothing else.
#
#   docker build -t geo-score-mcp .
#   docker run -i --rm --user "$(id -u)" -v "$PWD:/work" -e OPENAI_API_KEY geo-score-mcp
#
# Level 1 (score_site) needs no key. Pass only the keys you want with -e NAME (no value, so it stays out of
# your shell history and the client config); /work is where geo-score-watch.json and .geo-score/ live.
FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.jianruntech/geo-score" \
      org.opencontainers.image.title="geo-score" \
      org.opencontainers.image.description="Can AI engines cite your site, and do they? geo-score's MCP server over stdio." \
      org.opencontainers.image.source="https://github.com/jianruntech/geo-score" \
      org.opencontainers.image.licenses="MIT"

COPY cli/geo_score.py cli/geo_watch.py /app/
# without a mounted volume, runs can still be written (they are lost with the container)
RUN mkdir -p /work && chmod 1777 /work
WORKDIR /work
ENV GEO_SCORE_WATCH_CONFIG=/work/geo-score-watch.json \
    PYTHONIOENCODING=utf-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
USER 65534
ENTRYPOINT ["python3", "/app/geo_score.py", "mcp"]
