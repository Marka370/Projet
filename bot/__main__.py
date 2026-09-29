"""Point d'entrée.

    python -m bot           lance le bot (modération, tickets, rôles…)
    python -m bot setup     configure le serveur une fois puis s'arrête
    python -m bot check     vérifie config/server.yaml sans se connecter
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

import discord

from .client import CommunityBot, guild_id_from_env, token_from_env
from .config import Config, validate
from .setup_server import SetupError, apply_structure

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv est optionnel
    load_dotenv = None


def load_checked_config(path: str | None) -> Config:
    cfg = Config.load(path)
    errors = validate(cfg.data)
    if errors:
        print("❌ Erreurs dans la configuration :")
        for error in errors:
            print(f"   - {error}")
        raise SystemExit(1)
    return cfg


def pick_guild(client: discord.Client, guild_id: int | None) -> discord.Guild:
    if guild_id:
        guild = client.get_guild(guild_id)
        if guild is None:
            raise SetupError(
                f"Le bot n'est pas sur le serveur {guild_id}. Invite-le d'abord avec le lien du README."
            )
        return guild
    if len(client.guilds) == 1:
        return client.guilds[0]
    if not client.guilds:
        raise SetupError("Le bot n'est sur aucun serveur. Invite-le d'abord avec le lien du README.")
    raise SetupError("Le bot est sur plusieurs serveurs : indique lequel avec GUILD_ID.")


async def run_setup(cfg: Config, token: str, guild_id: int | None) -> int:
    client = discord.Client(intents=discord.Intents.default())
    client.cfg = cfg  # type: ignore[attr-defined]
    status = {"code": 0}

    @client.event
    async def on_ready() -> None:
        try:
            guild = pick_guild(client, guild_id)
            await apply_structure(guild, cfg, report=lambda line: print(line, flush=True))
        except SetupError as exc:
            print(f"❌ {exc}", flush=True)
            status["code"] = 1
        except discord.HTTPException as exc:
            print(f"❌ Erreur Discord : {exc}", flush=True)
            status["code"] = 1
        finally:
            await client.close()

    async with client:
        await client.start(token)
    return status["code"]


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m bot", description="Bot Discord communautaire")
    parser.add_argument("command", nargs="?", default="run", choices=["run", "setup", "check"])
    parser.add_argument("--config", help="chemin vers le fichier de configuration YAML")
    args = parser.parse_args()

    if load_dotenv is not None:
        load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    cfg = load_checked_config(args.config)
    if args.command == "check":
        print("✅ Configuration valide.")
        return

    token = token_from_env()
    guild_id = guild_id_from_env()
    try:
        if args.command == "setup":
            sys.exit(asyncio.run(run_setup(cfg, token, guild_id)))
        bot = CommunityBot(cfg, guild_id=guild_id, data_dir=os.getenv("DATA_DIR", "data"))
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        raise SystemExit("❌ Token invalide : vérifie DISCORD_TOKEN (régénère-le si besoin).")
    except discord.PrivilegedIntentsRequired:
        raise SystemExit(
            "❌ Active « Server Members Intent » et « Message Content Intent » dans le "
            "Developer Portal (onglet Bot), puis relance."
        )


if __name__ == "__main__":
    main()
