"""Modération automatique : invitations, spam, mentions abusives, mots interdits."""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from datetime import timedelta
from typing import Optional

import discord
from discord.ext import commands

from ..client import CommunityBot
from ..config import is_staff
from ..utils import send_log

INVITE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([a-zA-Z0-9-]+)",
    re.IGNORECASE,
)


class AutoMod(commands.Cog):
    def __init__(self, bot: CommunityBot):
        self.bot = bot
        self.recent: dict[tuple[int, int], deque[float]] = defaultdict(deque)
        settings = bot.cfg.bot.get("automod") or {}
        self.block_invites = bool(settings.get("block_invites", True))
        self.max_mentions = int(settings.get("max_mentions") or 0)
        spam = settings.get("spam") or {}
        self.spam_messages = int(spam.get("messages") or 0)
        self.spam_seconds = float(spam.get("seconds") or 0)
        self.timeout = timedelta(minutes=int(settings.get("timeout_minutes") or 10))
        words = [w for w in settings.get("banned_words") or [] if w]
        self.banned_re: Optional[re.Pattern[str]] = (
            re.compile(r"\b(?:" + "|".join(re.escape(w) for w in words) + r")\b", re.IGNORECASE)
            if words else None
        )

    async def _is_foreign_invite(self, message: discord.Message) -> bool:
        assert message.guild
        for code in INVITE_RE.findall(message.content):
            try:
                invite = await self.bot.fetch_invite(code)
            except discord.HTTPException:
                return True  # invitation invalide ou expirée : on supprime quand même
            if invite.guild is None or invite.guild.id != message.guild.id:
                return True
        return False

    def _is_spam(self, message: discord.Message) -> bool:
        if not self.spam_messages or not self.spam_seconds:
            return False
        assert message.guild
        now = time.monotonic()
        history = self.recent[(message.guild.id, message.author.id)]
        history.append(now)
        while history and now - history[0] > self.spam_seconds:
            history.popleft()
        if len(history) > self.spam_messages:
            history.clear()
            return True
        return False

    async def _punish(self, message: discord.Message, reason: str, *, timeout: bool) -> None:
        member = message.author
        assert isinstance(member, discord.Member) and message.guild
        self.bot.automod_deleted.add(message.id)
        try:
            await message.delete()
        except discord.HTTPException:
            self.bot.automod_deleted.discard(message.id)
        applied = ""
        if timeout:
            try:
                await member.timeout(self.timeout, reason=f"Automod : {reason}")
                applied = f" et rendu muet {int(self.timeout.total_seconds() // 60)} min"
            except discord.HTTPException:
                pass
        try:
            await message.channel.send(
                f"⛔ {member.mention}, ton message a été supprimé : {reason}{applied}.", delete_after=10
            )
        except discord.HTTPException:
            pass
        embed = discord.Embed(
            description=f"🤖 Automod : message de {member.mention} supprimé dans {message.channel.mention}",
            colour=discord.Colour.red(),
        )
        embed.add_field(name="Raison", value=reason + applied, inline=False)
        embed.add_field(name="Contenu", value=(message.content or "*(vide)*")[:1000], inline=False)
        embed.set_footer(text=f"ID : {member.id}")
        await send_log(self.bot, message.guild, embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot or not isinstance(message.author, discord.Member):
            return
        if is_staff(message.author):
            return

        if self._is_spam(message):
            await self._punish(message, "spam (trop de messages d'affilée)", timeout=True)
            return
        mentions = len(message.raw_mentions) + len(message.raw_role_mentions)
        if message.mention_everyone:
            mentions += self.max_mentions or 1
        if self.max_mentions and mentions > self.max_mentions:
            await self._punish(message, "trop de mentions", timeout=True)
            return
        if self.banned_re and self.banned_re.search(message.content):
            await self._punish(message, "langage interdit", timeout=False)
            return
        if self.block_invites and INVITE_RE.search(message.content) and await self._is_foreign_invite(message):
            await self._punish(message, "publicité pour un autre serveur interdite", timeout=False)


async def setup(bot: CommunityBot) -> None:
    await bot.add_cog(AutoMod(bot))
