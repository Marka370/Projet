"""Journal des messages supprimés et modifiés."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..client import CommunityBot
from ..utils import send_log


def _clip(text: str, limit: int = 1000) -> str:
    text = text or "*(vide)*"
    return text if len(text) <= limit else text[: limit - 1] + "…"


class Logs(commands.Cog):
    def __init__(self, bot: CommunityBot):
        self.bot = bot

    def _ignored(self, message: discord.Message) -> bool:
        if message.guild is None or message.author.bot:
            return True
        logs = self.bot.cfg.channel(message.guild, "logs")
        return logs is not None and message.channel.id == logs.id

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        if message.id in self.bot.automod_deleted:
            self.bot.automod_deleted.discard(message.id)
            return
        if self._ignored(message):
            return
        embed = discord.Embed(
            description=f"🗑️ Message de {message.author.mention} supprimé dans {message.channel.mention}",
            colour=discord.Colour.red(),
        )
        embed.add_field(name="Contenu", value=_clip(message.content), inline=False)
        if message.attachments:
            embed.add_field(
                name="Pièces jointes",
                value=_clip("\n".join(a.filename for a in message.attachments)),
                inline=False,
            )
        embed.set_footer(text=f"Auteur : {message.author} ({message.author.id})")
        await send_log(self.bot, message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if self._ignored(after) or before.content == after.content:
            return
        embed = discord.Embed(
            description=(
                f"✏️ {after.author.mention} a modifié [un message]({after.jump_url}) "
                f"dans {after.channel.mention}"
            ),
            colour=discord.Colour.orange(),
        )
        embed.add_field(name="Avant", value=_clip(before.content), inline=False)
        embed.add_field(name="Après", value=_clip(after.content), inline=False)
        embed.set_footer(text=f"Auteur : {after.author} ({after.author.id})")
        await send_log(self.bot, after.guild, embed)


async def setup(bot: CommunityBot) -> None:
    await bot.add_cog(Logs(bot))
