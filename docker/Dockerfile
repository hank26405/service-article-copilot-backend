# Use the official Python SLIM image based on Debian 12 (Bookworm), which is stable
FROM python:3.11-slim

# --- Environment Variables ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ="Asia/Taipei"
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# --- User and Directory Setup ---
ARG APP_USER=app
ARG APP_GROUP=app
ARG PROJECT_PATH="/home/${APP_USER}/workdir"
# 1. 是否啟用 Zscaler 憑證修復 (預設 false，只有 Local build 傳入 true)
ARG USE_ZSCALER=false

# Set project path and PYTHONPATH
ENV PROJECT_PATH=${PROJECT_PATH}
ENV PYTHONPATH=${PROJECT_PATH}

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 設定 Python/Requests SSL 憑證路徑 (指向系統標準位置)
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

ENV NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/zscaler.crt
# --- System Setup (run as root) - 安裝必要的系統依賴 ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # 基礎工具
    curl wget gnupg ca-certificates libmagic1 locales \
    # PDF 處理依賴
    poppler-utils libpoppler-dev python3-poppler-qt5 \
    # 圖像處理依賴
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
    # 中文字體
    fonts-noto-cjk fonts-wqy-zenhei fontconfig && \
    # 設定語系支援中文
    echo "zh_TW.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "zh_CN.UTF-8 UTF-8" >> /etc/locale.gen && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    locale-gen && \
    # 更新字體快取
    fc-cache -fv && \
    # 設定時區
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # 清理快取以減少映像大小
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

    # --- [關鍵步驟] 智慧憑證安裝 ---
# 技巧: 使用 zscaler.crt* (星號)，若檔案不存在不會報錯
COPY zscaler.crt* /tmp/zscaler_input.crt

# 邏輯判斷:
# 1. 如果 USE_ZSCALER=true 且有檔案 -> 安裝憑證 (Local)
# 2. 否則 -> 建立空檔案 (Prod)，避免 Node.js 讀取變數時報錯
RUN if [ "$USE_ZSCALER" = "true" ] && [ -f "/tmp/zscaler_input.crt" ]; then \
        echo "✅ Detected Zscaler mode. Installing certificate..."; \
        mv /tmp/zscaler_input.crt /usr/local/share/ca-certificates/zscaler.crt; \
        chmod 644 /usr/local/share/ca-certificates/zscaler.crt; \
        update-ca-certificates; \
    else \
        echo "🚀 Standard mode. Skipping Zscaler CA update."; \
        touch /usr/local/share/ca-certificates/zscaler.crt; \
    fi

# --- User and Directory Creation (run as root) ---
RUN groupadd -r ${APP_GROUP} && \
    useradd -r -g ${APP_GROUP} -m -d ${PROJECT_PATH} -s /sbin/nologin ${APP_USER} && \
    mkdir -p ${PROJECT_PATH}/data/logs && \
    chown -R ${APP_USER}:${APP_GROUP} ${PROJECT_PATH}

# Set working directory
WORKDIR ${PROJECT_PATH}

RUN mkdir -p article_copilot

# --- Copy dependency files ---
COPY --chown=${APP_USER}:${APP_GROUP} pyproject.toml uv.lock ./

# --- Dependency Installation (run as root) ---
RUN python3 -m pip install --default-timeout=300 --retries=5 --no-cache-dir ".[dev]"

# --- Copy Application Code ---
COPY --chown=${APP_USER}:${APP_GROUP} article_copilot/ ./article_copilot/
COPY --chown=${APP_USER}:${APP_GROUP} docker/start.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start.sh



# --- Switch to non-privileged user ---
USER ${APP_USER}

# Expose application port
EXPOSE 8888


ENTRYPOINT ["start.sh"]