"""This file define the health check base model object"""
from pydantic import BaseModel

class HealthCheckBaseModel(BaseModel):
    """This class define the response of the health check"""
    version: str
    msg: str
    error: str
