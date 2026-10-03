from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from vald_fc_bot.bot import ValdFCBot
from vald_fc_bot.commands import ValdFCCog, verify_command_parity

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("vald_fc_bot")


async def check_commands() -> int:
    """Check that every intended command exists in both command interfaces."""
    bot = ValdFCBot()
    try:
        await bot.add_cog(ValdFCCog(bot))
        prefix_names, slash_names = verify_command_parity(bot)
        print("Command parity check passed.")
        print("Prefix commands: " + ", ".join(f"%{name}" for name in sorted(prefix_names)))
        print("Slash commands:  " + ", ".join(f"/{name}" for name in sorted(slash_names)))
        return 0
    finally:
        await bot.close()


async def run_bot(token: str) -> None:
    bot = ValdFCBot()
    async with bot:
        await bot.add_cog(ValdFCCog(bot))
        await bot.start(token)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Vald FC Discord bot.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify that all prefix and slash commands are registered without connecting to Discord",
    )
    args = parser.parse_args()

    if args.check:
        return asyncio.run(check_commands())

    token = os.environ.get("DISCORD_TOKEN", "").strip()
    if not token:
        print(
            "Missing DISCORD_TOKEN. Add your Discord bot token to Replit Secrets, "
            "then run the bot again.",
            file=sys.stderr,
        )
        return 1

    try:
        asyncio.run(run_bot(token))
    except KeyboardInterrupt:
        logger.info("Bot stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
