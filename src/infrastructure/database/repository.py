from typing import Any

from sqlalchemy import CompoundSelect, Result, Select, func, select

from src.infrastructure import errors

from .cqs import Command, Query


class Repository:
    """``Repository`` is a high level abstraction to work with the database.

    notes:
        under the hood ``Repository`` encapsulates CQRS to trigger commands or
        queries for different operations. this is need becuase the 'async'
        approach is used and this is why we should separate 'query'
        and 'command' philosophical concepts to properly work with
        SQLAclhemy session scopes.

    links:
        https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks


    usage:
    ```py
        # using transactions to rollback changes
        async with transaction() as session:
            john: database.User = await UserRepository().add_user(john_candidate)
            await sesison.flush()
            configuration_candidate.user_id = john.id
            config: UserConfig = await ConfigurationRepository().add_user(
                configuration_candidate
            )
    ```

    ```py
        # insert concurrently
        async with transaction():
            tasks = [
                UserRepository().add_user(john_candidate),
                UserRepository().add_user(marry_candidate)
            ]
            results = await asyncio.gather(*tasks)
    ```

    ```py
        # get concurrently
        tasks = [
            UserRepository().get_user(id_=1),
            UserRepository().get_user(id_=2)
        ]
        results = await asyncio.gather(*tasks)
    ```
    """  # noqa: E501

    query = Query()
    command = Command()

    async def count(self, table, **filters) -> int:
        """get the number of items in a table"""

        _filters: dict = {
            key: value for key, value in filters.items() if value
        }

        try:
            query: Select = select(func.count(getattr(table, "id")))
            for attr, value in _filters:
                query = getattr(query, "where")(getattr(table, attr) == value)
        except AttributeError as error:
            raise errors.DatabaseError(
                f"``id`` does not exist for {table} "
            ) from error

        async with self.query.session as session:
            async with session.begin():
                result: Result = await session.execute(query)
                value = result.scalar()

                if not isinstance(value, int):
                    raise errors.DatabaseError(
                        message=(
                            "Database count() function returned no-integer "
                            f"({type(value)}) type of value"
                        ),
                    )
                else:
                    return value

    def _add_pagination_filters(
        self, query, /, offset: int = 0, limit: int = 10, **_
    ):
        """update the query if pagination filters are specified.

        params:
            ``offset: int | None`` to apply filter `OFFSET {last_id}`
            ``limit: int | None`` to apply filter `LIMIT {limit}`
        """

        if offset < 0:
            raise ValueError("Wrong ``offset`` on pagination")
        elif offset > 0:
            query = query.offset(offset)

        if limit < 0:
            raise ValueError("Wrong ``limit`` on pagination")
        elif limit > 0:
            query = query.limit(limit)

        return query
