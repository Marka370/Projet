"""Accueil des nouveaux membres et journal des arrivées/départs."""

from __future__ import annotations

from datetime import datetime, timezone

import discord
from discord.ext import commands

from ..client import CommunityBot
from ..utils import send_log


class Welcome(commands.Cog):
    def __init__(self, bot: CommunityBot):
        self.bot = bot

    def _mention(self, guild: discord.Guild, key: str, fallback: str) -> str:
        channel = self.bot.cfg.channel(guild, key)
        return channel.mention if channel else fallback

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        guild = member.guild
        cfg = self.bot.cfg
        channel = cfg.channel(guild, "welcome")
        template = cfg.bot.get("welcome_message") or "Bienvenue {member} !"
        if isinstance(channel, discord.TextChannel):
            text = template.format(
                member=member.mention,
                name=member.display_name,
                server=guild.name,
                count=guild.member_count,
                rules=self._mention(guild, "rules", "règlement"),
                verification=self._mention(guild, "verification", "vérification"),
            )
            embed = discord.Embed(description=text.strip(), colour=discord.Colour.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            try:
                await channel.send(embed=embed)
            except discord.HTTPException:
                pass

        age = datetime.now(timezone.utc) - member.created_at
        embed = discord.Embed(
            description=f"📥 {member.mention} a rejoint le serveur ({guild.member_count} membres)",
            colour=discord.Colour.green(),
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name="Compte créé", value=discord.utils.format_dt(member.created_at, "R"))
        min_days = int(cfg.bot.get("new_account_days") or 0)
        if min_days and age.days < min_days:
            embed.colour = discord.Colour.orange()
            embed.add_field(name="⚠️ Attention", value=f"Compte récent (moins de {min_days} jours)")
        embed.set_footer(text=f"ID : {member.id}")
        await send_log(self.bot, guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        roles = [r.mention for r in reversed(member.roles) if r != member.guild.default_role]
        embed = discord.Embed(
            description=f"📤 {member.mention} a quitté le serveur",
            colour=discord.Colour.dark_grey(),
        )
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        if roles:
            embed.add_field(name="Rôles", value=" ".join(roles)[:1024])
        embed.set_footer(text=f"ID : {member.id}")
        await send_log(self.bot, member.guild, embed)


async def setup(bot: CommunityBot) -> None:
    await bot.add_cog(Welcome(bot))
