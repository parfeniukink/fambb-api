"""
This is an application entrypoint.
What is the best way to document the project? I think that each project it
is some sort of a story... Maybe it comes from my personal but it still being
my pet-project, right?

So this project is a story about ASGI-server, called 'John'. From another
point of view I believe that John is a human-asgi representation of a client
of this application.

Technical notes could be pasted along with a story if it improves
reading experience.

Let's start a story. ༼ つ ◕_◕ ༽つ━☆ﾟ.*･｡ﾟ.

**************************************************

This is a book about John. He is ASGI-server to provide financial features
for people (us). ASGI is a low-level universe system which does not care about
people's (our) world, he just lives his own life in 'ASGI world'.

All ASGI servers loves to run, did you know?
Our server runs all the circle by circle. To see how John makes shit:
```
# let's go John!!!
uvicorn src.main:app --reload
```

Also, John can run with 'uvloop doping'. You just inject this into
his blood and John just become another ASGI-boy. Peple usually need that
in production I believe.
```
# use 'uvloop doping' John!!!
uvicorn src.main:app --reload --loop uvloop
```

But how ASGI servers run? We know that people run with legs, but ASGIs don't
have those, right? I am not sure...

John is quite nice buddy and super-organized in his life. Classic-boy.

```

usage callstack:
        ↓ main
        ↓ rest
        ↓ contracts
        ↓ operational
        ↓ domain
        ↓ infrastructure
        ↓ config

```

Alright. Remember I told you about ASGI servers can run?
So they run "for something". What does it mean? Well, people "need features".
ASGI servers "run for those". In order to do that they need routes (paths).

So, getting back to John, he actually works in a bank. So John run for
some financial operations. If humans need to see the analytics of their
transactions John run for it.

The world of ASGI servers is quite misterious, right? Where John take
this analytics, right? Let's go step by step. Let's be detectives.
First of all, where usually John goes? Really, who is John from terms,
that people (clients, ```REST clients```) can understand?

Go to page: src/rest/__init__.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src import rest
from src.config import settings
from src.infrastructure import errors, factories, middleware

logger.add(
    settings.logging.file,
    format=settings.logging.format,
    rotation=settings.logging.rotation,
    compression=settings.logging.compression,
    level=settings.logging.level,
)


exception_handlers = (
    {
        ValueError: errors.value_error_handler,
        RequestValidationError: errors.unprocessable_entity_error_handler,
        HTTPException: errors.fastapi_http_exception_handler,
        errors.BaseError: errors.base_error_handler,
        NotImplementedError: errors.not_implemented_error_handler,
        Exception: errors.unhandled_error_handler,
    }
    if settings.debug is False
    else {}
)

app: FastAPI = factories.asgi_app(
    debug=settings.debug,
    rest_routers=(
        rest.analytics.router,
        rest.costs.router,
        rest.incomes.router,
        rest.exchange.router,
        rest.currencies.router,
        rest.users.router,
    ),
    middlewares=(
        (CORSMiddleware, middleware.FASTAPI_CORS_MIDDLEWARE_OPTIONS),
    ),
    exception_handlers=exception_handlers,
)
