"""This file is for utility function"""
from functools import lru_cache
import tzlocal
import tomllib
import uuid
from article_copilot.configs.logger_setting import log


LOCAL_TIMEZONE = tzlocal.get_localzone()

@lru_cache(maxsize=128, typed=False)
def health_check_parsing() -> str:
    """
    Parse the project version from pyproject.toml.

    Returns:
        version_str: str, the version defined in pyproject.toml [project].version
    """
    with open('pyproject.toml', 'rb') as f:
        pyproject_data = tomllib.load(f)
    
    return pyproject_data['project']['version']

def generate_id():
    """Generate and return an id."""
    return uuid.uuid1()