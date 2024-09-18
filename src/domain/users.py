from collections.abc import AsyncGenerator

from src.infrastructure.entities import InternalData


class UserFlat(InternalData):
    id: int
    name: str


class UserRepository:
    _storage = [
        UserFlat(id=1, name="John Doe"),
        UserFlat(id=2, name="Marry Doe"),
    ]

    async def all(self) -> AsyncGenerator[UserFlat, None]:
        for item in self._storage:
            yield item

    async def get(self, id_: int) -> UserFlat:
        for item in self._storage:
            if item.id == id_:
                return item

        raise Exception(f"User {id_} is not found")
