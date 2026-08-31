"""Single entrypoint for all application database seeds.

Run from the repository root:

    python setup_seeds.py

The workflow is idempotent and executes in dependency order:

1. roles;
2. permissions;
3. exact role-permission mappings.
"""

from __future__ import annotations

import asyncio
import logging

from seeds.__main__ import main


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )
    asyncio.run(main())
