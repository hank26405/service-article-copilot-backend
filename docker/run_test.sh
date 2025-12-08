#!/bin/bash

# 退回上一層目錄 (根據您原始腳本)
cd ..

# 設定環境變數
export PROJECT_DIR=/home/app/workdir
export DOCKER_NETWORK_NAME=test-ems-ai-network

docker build -t my-python-uv-tester -f ./docker/test/test-dockerfile .

# --- 測試環境設定 ---

# 建立 Docker 網路
echo "Creating Docker network: $DOCKER_NETWORK_NAME"
docker network create $DOCKER_NETWORK_NAME

docker run -itd --network $DOCKER_NETWORK_NAME --expose=6379 --name test-redis redis:6.0-alpine

docker run -itd --network $DOCKER_NETWORK_NAME --expose=27017 --name test-mongo mongo:latest

docker run --rm --user root --network $DOCKER_NETWORK_NAME \
  --env-file $(pwd)/docker/test/test.env \
  -v $(pwd):$PROJECT_DIR \
  -w $PROJECT_DIR \
  -e PYTHONPATH=$PROJECT_DIR \
  -e SECRET_TOKEN=test_secret_token \
  my-python-uv-tester /bin/bash -c " \
    echo 'Starting pytest...'; \
    pytest -q -p no:warnings \
      --cov=article_copilot \
      --cov-report term-missing \
      --cov-config=.coveragerc \
      -o log_cli=true --capture=no tests/ \
  "

# --- 清理環境 ---

echo "Cleaning up containers and network..."
docker rm -f test-redis
docker network rm $DOCKER_NETWORK_NAME

echo "Test script finished."

# 回到原本的目錄 (根據您原始腳本)
cd docker