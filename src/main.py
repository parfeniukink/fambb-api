from fastapi import FastAPI
from loguru import logger

from src import rest
from src.config import settings
from src.infrastructure import web_application_factory

# Adjust the logging
# -------------------------------
logger.add(
    settings.logging.file,
    format=settings.logging.format,
    rotation=settings.logging.rotation,
    compression=settings.logging.compression,
    level=settings.logging.level,
)


# Adjust the application
# -------------------------------
app: FastAPI = web_application_factory(
    debug=settings.debug,
    rest_routers=(rest.analytics_router,),
)
