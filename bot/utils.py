"""Fonctions utilitaires partagées."""

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING, Optional

import discord

if TYPE_CHECKING:
    from .client import CommunityBot

MAX_TIMEOUT = timedelta(days=28)
_DURATION_RE = re.compile(r"(\d+)\s*(sec|min|s|m|h|j|d)", re.IGNORECASE)
_UNITS = {"s": 1, "sec": 1, "m": 60, "min": 60, "h": 3600, "j": 86400, "d": 86400}


def parse_duration(text: str) -> Optional[timedelta]:
    """Convertit « 10m », « 2h », « 1j », « 1h30m »… en timedelta (None si invalide)."""
    text = text.strip().lower().replace(" ", "")
    if not text:
        return None
    total, consumed = 0, 0
    for match in _DURATION_RE.finditer(text):
        if match.start() != consumed:
            return None
        total += int(match.group(1)) * _UNITS[match.group(2).lower()]
        consumed = match.end()
    if consumed != len(text) or total <= 0:
        return None
    return timedelta(seconds=total)


def format_duration(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    parts = []
    for unit, size in (("j", 86400), ("h", 3600), ("min", 60), ("s", 1)):
        value, seconds = divmod(seconds, size)
        if value:
            parts.append(f"{value} {unit}")
    return " ".join(parts) or "0 s"


def colour(value: Optional[str], default: discord.Colour = discord.Colour.blurple()) -> discord.Colour:
    if not value:
        return default
    try:
        return discord.Colour.from_str(str(value))
    except ValueError:
        return default


async def send_log(
    bot: "CommunityBot",
    guild: discord.Guild,
    embed: discord.Embed,
    *,
    channel_key: str = "logs",
    file: Optional[discord.File] = None,
) -> None:
    channel = bot.cfg.channel(guild, channel_key)
    if not isinstance(channel, discord.TextChannel):
        return
    try:
        if file is not None:
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)
    except discord.HTTPException:
        pass


def can_act_on(actor: discord.Member, target: discord.Member) -> Optional[str]:
    """Vérifie la hiérarchie des rôles. Retourne un message d'erreur ou None."""
    guild = actor.guild
    if target == actor:
        return "Tu ne peux pas te sanctionner toi-même."
    if target == guild.owner:
        return "Impossible de sanctionner le propriétaire du serveur."
    if target.bot and target == guild.me:
        return "Je ne peux pas me sanctionner moi-même."
    if actor != guild.owner and target.top_role >= actor.top_role:
        return "Ce membre a un rôle égal ou supérieur au tien."
    if target.top_role >= guild.me.top_role:
        return "Ce membre a un rôle égal ou supérieur au mien : place mon rôle plus haut dans la liste des rôles."
    return None
