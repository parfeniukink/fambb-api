"""
---
this package is responsible for exposing user-related HTTP resources.
simply user-related endpoints.
---

STORY ༼ つ ◕_◕ ༽つ━☆ﾟ.*･｡ﾟ

John used to work with different clients and this is why he uses
'User Profile Shelf'. it is a phisical shelf where John keeps pepers
with clients preferences. the shelf is always organized which means
that the searching process takes about 'nothing'.

clients commonly ask about their preferences. this is mostly
because of the curiocity. like people check their settings
from time to time.

also, over the time clients can come for changing their settings.
like in a real life you can disable SMS (or email) notifications from
your bank not to be distructed.

John is not that flexible, clients can customize default currency,
default cost category, costs and incomes snippets.
most of these preferences are used for future communication with John.
imagine that you are in rush and you tell John information about your last
cost. if you forget to tell about the currency or the category - John won't
request that information from you. the 'User Profile Shelf' is exactly
for that purpose: John don't remember everything, right?
so clients preferences are kept to be reused in future...
"""

from fastapi import APIRouter, Body, Depends

from src import operational as op
from src.domain import users as domain
from src.infrastructure import Response, database

from ..contracts.users import User, UserConfigurationPartialUpdateRequestBody

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def user_retrieve(
    user: domain.User = Depends(op.authorize),
) -> Response[User]:
    """Retrieve current user information information."""

    return Response[User](result=User.from_instance(user))


@router.patch("/configuration")
async def parial_update_user_configuration(
    user: domain.User = Depends(op.authorize),
    body: UserConfigurationPartialUpdateRequestBody = Body(...),
) -> None:
    """Update the user configuration partially."""

    async with database.transaction():
        await domain.UserRepository().update_user_configuration(
            user_id=user.id, **body.model_dump(exclude_unset=True)
        )
