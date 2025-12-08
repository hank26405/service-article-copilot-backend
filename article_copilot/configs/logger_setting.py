"""This file is used in setting config."""

# import relation package.
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import socket

# import project package.
from article_copilot.configs.project_setting import service_config


def get_logger():
    """Get the custom logging"""
    ip_address = socket.gethostbyname(socket.gethostname())
    host_name = socket.gethostname()
    system_name = service_config.system_name

    log_format = f"[LogTimeStamp:%(asctime)s][Host:{host_name}][IP:{ip_address}][Level:%(levelname)s][SystemName:{system_name}][ThreadName:%(threadName)s][SessionID:NA][PgName:%(funcName)s] - %(message)s"
    date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    
    if not os.path.exists(service_config.log_file_path):
        os.makedirs(service_config.log_file_path, exist_ok=True)

    log_filename = f"{service_config.log_file_path}{host_name}-access.log"
    handler = TimedRotatingFileHandler(
        log_filename, when='midnight', encoding='utf-8')

    formatter = logging.Formatter(log_format, datefmt=date_format)
    handler.setFormatter(formatter)
    handler.suffix = '.%Y-%m-%d'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            handler,
            logging.StreamHandler()
        ]
    )
    # commente first because we need to look
    logging.getLogger('apscheduler.executors.default').propagate = False
    return logging


log = get_logger()
