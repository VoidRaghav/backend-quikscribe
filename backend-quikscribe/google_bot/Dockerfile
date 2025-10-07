# NEW: Bun-based Dockerfile for dynamic port support
FROM oven/bun:1

WORKDIR /app

# Install ffmpeg for recording
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY package.json .
COPY bun.lock .

RUN bun install

COPY . .

# ✅ EXPOSE DYNAMIC PORT (will be set at runtime)
EXPOSE ${DYNAMIC_PORT:-3000}

# Set environment variable for dynamic port
ENV DYNAMIC_PORT=3000

CMD ["bun", "run", "index.ts"]

# OLD CODE - COMMENTED OUT FOR REFERENCE:
# FROM selenium/standalone-chrome:4.31.0-20250414
# 
# USER root
# RUN apt-get update && \
#     apt-get install -y ffmpeg xvfb fluxbox x11vnc curl jq pulseaudio && \
#     mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix && \
#     rm -rf /var/lib/apt/lists/*
# 
# USER seluser
# 
# ENV DISPLAY=:99 \   
#     SCREEN_RES=1280x720x24 \
#     SE_NODE_OVERRIDE_MAX_SESSIONS=true \
#     SE_NODE_MAX_SESSIONS=1
# 
# WORKDIR /app
# 
# RUN curl -fsSL https://bun.sh/install | bash
# ENV PATH="/home/seluser/.bun/bin:${PATH}"
# 
# COPY --chown=seluser:seluser . .
# 
# RUN bun install
# 
# COPY --chown=seluser:seluser entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh
# 
# ENTRYPOINT ["/entrypoint.sh"]