"""
CLI script for creating cost categories in the database.

Usage:
    python -m scripts.create_cost_category --name "🍔 Food"
    python -m scripts.create_cost_category -n "🚗 Transport" -n "🏠 Housing"
"""

import argparse
import asyncio
import sys

from src.infrastructure import database


async def main() -> int:
    """Create cost categories in the database."""
    parser = argparse.ArgumentParser(
        description="Create cost categories in the database"
    )
    parser.add_argument(
        "-n",
        "--name",
        action="append",
        required=True,
        help="Category name (can be specified multiple times)",
    )

    args = parser.parse_args()

    created_categories = []

    try:
        async with database.transaction() as session:
            for category_name in args.name:
                category = database.CostCategory(name=category_name)
                session.add(category)
                await session.flush()
                created_categories.append(
                    {"id": category.id, "name": category_name}
                )

        print(
            f"\n{len(created_categories)} "
            f"{'category' if len(created_categories) == 1 else 'categories'} "
            f"created successfully!"
        )
        print("\nCreated categories:")
        for cat in created_categories:
            print(f"\n  ID {cat['id']}: {cat['name']}")

    except Exception as e:
        print(f"Error creating cost categories: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
else:
    raise SystemExit("Sorry, this module can not be imported")
