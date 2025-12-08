#!/bin/bash

# 切換到項目根目錄
cd ..

# 停止並移除現有容器（如果存在）
echo "Stopping existing container..."
docker stop image-llm-agent 2>/dev/null || true
docker rm image-llm-agent 2>/dev/null || true


mkdir -p /home/hankliang/data/database /home/hankliang/data/article_copilot /home/hankliang/data/article_copilot/logs
chmod a+w /home/hankliang/data/article_copilot/logs /home/hankliang/data/database/

# 構建 Docker 映像
echo "Building Docker image..."
# docker build --no-cache -f docker/Dockerfile -t image-llm-agent .
docker build -f docker/Dockerfile -t image-llm-agent .

# 返回 docker 目錄
cd docker