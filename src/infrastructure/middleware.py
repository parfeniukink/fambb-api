from src.config import settings

# NOTE: For more information:
#       fastapi.middleware.cors.CORSMiddleware
FASTAPI_CORS_MIDDLEWARE_OPTIONS: dict = {
    "allow_origins": settings.cors.allow_origins,
    "allow_credentials": settings.cors.allow_credentials,
    "allow_methods": settings.cors.allow_methods,
    "allow_headers": settings.cors.allow_headers,
    "expose_headers": settings.cors.expose_headers,
    "max_age": settings.cors.max_age,
}
