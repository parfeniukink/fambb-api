"""CLI script for setting user password hash in the database.

Usage:
    python -m scripts.set_password --id 2 --password admin
    python -m scripts.set_password -i 2 -p admin
"""

import argparse
import asyncio
import sys

from sqlalchemy import select

from src.infrastructure import database, security


async def main() -> int:
    """Update user password hash in the database."""
    parser = argparse.ArgumentParser(
        description="Set user password hash in the database"
    )
    parser.add_argument(
        "-i", "--id", required=True, type=int, help="User ID to update"
    )
    parser.add_argument(
        "-p", "--password", required=True, help="New password for the user"
    )

    args = parser.parse_args()

    try:
        # Hash password with Argon2
        password_hash = security.hash_password(args.password)

        # Update user password
        async with database.transaction() as session:
            result = await session.execute(
                select(database.User).where(database.User.id == args.id)
            )
            user = result.scalar_one_or_none()

            if user is None:
                print(
                    f"Error: User with ID {args.id} not found",
                    file=sys.stderr,
                )
                return 1

            user.password_hash = password_hash
            await session.flush()

        print(f"\nPassword updated successfully for user ID {args.id}!")

    except Exception as e:
        print(f"Error updating password: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
else:
    raise SystemExit("Sorry, this module can not be imported")
