"""Le bot principal."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands

from .config import Config
from .db import Database
from .views import register_persistent_views

log = logging.getLogger("bot")

EXTENSIONS = (
    "bot.cogs.welcome",
    "bot.cogs.moderation",
    "bot.cogs.automod",
    "bot.cogs.logs",
    "bot.cogs.utility",
)


class CommunityBot(commands.Bot):
    def __init__(self, cfg: Config, guild_id: Optional[int] = None, data_dir: str | Path = "data"):
        intents = discord.Intents.default()
        intents.members = True          # arrivées / départs
        intents.message_content = True  # automod et logs de messages
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
            activity=discord.Game("/aide"),
        )
        self.cfg = cfg
        self.guild_id = guild_id
        self.db = Database(Path(data_dir) / "bot.sqlite3")
        # Messages supprimés par l'automod (déjà journalisés, à ne pas relogger).
        self.automod_deleted: set[int] = set()

    async def setup_hook(self) -> None:
        for extension in EXTENSIONS:
            await self.load_extension(extension)
        register_persistent_views(self)
        if self.guild_id:
            guild = discord.Object(id=self.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        log.info("%d commandes slash synchronisées", len(synced))

    async def on_ready(self) -> None:
        log.info("Connecté en tant que %s (%s)", self.user, self.user and self.user.id)
        for guild in self.guilds:
            log.info("  - serveur : %s (%s)", guild.name, guild.id)

    async def close(self) -> None:
        self.db.close()
        await super().close()


def token_from_env() -> str:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "❌ Variable DISCORD_TOKEN manquante. Mets le token de ton bot dans le fichier .env "
            "ou dans les variables d'environnement de ton hébergeur."
        )
    return token


def guild_id_from_env() -> Optional[int]:
    value = os.getenv("GUILD_ID", "").strip()
    if not value:
        return None
    if not value.isdigit():
        raise SystemExit("❌ GUILD_ID doit être un nombre (l'identifiant du serveur).")
    return int(value)
