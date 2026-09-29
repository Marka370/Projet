"""Commandes pratiques : aide, infos, sondages, annonces, mise en place."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from ..client import CommunityBot
from ..setup_server import SetupError, apply_structure

NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

HELP_MEMBERS = """
`/aide` — cette aide
`/sondage` — créer un sondage
`/serveur` — infos sur le serveur
`/profil` — infos sur un membre
"""

HELP_STAFF = """
`/warn` `/warns` `/unwarn` `/clearwarns` — avertissements
`/mute` `/unmute` — rendre muet (ex. durée : 10m, 2h, 1j)
`/kick` `/ban` `/unban` — expulser / bannir
`/clear` — supprimer des messages
`/slowmode` `/lock` `/unlock` — gérer un salon
`/annonce` — publier une annonce
`/setup` — (ré)appliquer la structure du serveur
"""


class Utility(commands.Cog):
    def __init__(self, bot: CommunityBot):
        self.bot = bot

    @app_commands.command(name="aide", description="Liste des commandes du bot")
    async def aide(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title="📖 Commandes", colour=discord.Colour.blurple())
        embed.add_field(name="Pour tout le monde", value=HELP_MEMBERS.strip(), inline=False)
        member = interaction.user
        if isinstance(member, discord.Member) and member.guild_permissions.moderate_members:
            embed.add_field(name="Staff", value=HELP_STAFF.strip(), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="serveur", description="Informations sur le serveur")
    @app_commands.guild_only()
    async def serveur(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        assert guild
        embed = discord.Embed(title=guild.name, colour=discord.Colour.blurple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👥 Membres", value=str(guild.member_count))
        embed.add_field(name="💬 Salons", value=str(len(guild.channels)))
        embed.add_field(name="🎭 Rôles", value=str(len(guild.roles) - 1))
        embed.add_field(name="🚀 Boosts", value=f"{guild.premium_subscription_count} (niveau {guild.premium_tier})")
        embed.add_field(name="📅 Créé", value=discord.utils.format_dt(guild.created_at, "D"))
        if guild.owner_id:
            embed.add_field(name="👑 Propriétaire", value=f"<@{guild.owner_id}>")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profil", description="Informations sur un membre")
    @app_commands.describe(membre="Le membre (toi par défaut)")
    @app_commands.guild_only()
    async def profil(self, interaction: discord.Interaction, membre: discord.Member | None = None) -> None:
        member = membre or interaction.user
        assert isinstance(member, discord.Member)
        embed = discord.Embed(title=member.display_name, colour=member.colour)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Compte créé", value=discord.utils.format_dt(member.created_at, "D"))
        if member.joined_at:
            embed.add_field(name="A rejoint", value=discord.utils.format_dt(member.joined_at, "D"))
        roles = [r.mention for r in reversed(member.roles) if r != member.guild.default_role]
        embed.add_field(name=f"Rôles ({len(roles)})", value=" ".join(roles)[:1024] or "Aucun", inline=False)
        embed.set_footer(text=f"ID : {member.id}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="sondage", description="Créer un sondage")
    @app_commands.describe(
        question="La question",
        choix="Les choix séparés par ; (ex. Pizza;Burger;Sushi). Vide = Oui/Non",
    )
    @app_commands.guild_only()
    async def sondage(self, interaction: discord.Interaction, question: str, choix: str = "") -> None:
        options = [c.strip() for c in choix.split(";") if c.strip()]
        if len(options) == 1 or len(options) > len(NUMBER_EMOJIS):
            await interaction.response.send_message(
                f"❌ Donne entre 2 et {len(NUMBER_EMOJIS)} choix séparés par ; (ou aucun pour Oui/Non).",
                ephemeral=True,
            )
            return
        if options:
            emojis = NUMBER_EMOJIS[: len(options)]
            description = "\n".join(f"{e} {o}" for e, o in zip(emojis, options))
        else:
            emojis = ["👍", "👎"]
            description = "👍 Oui\n👎 Non"
        embed = discord.Embed(title=f"📊 {question}", description=description, colour=discord.Colour.blurple())
        embed.set_footer(text=f"Sondage de {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for emoji in emojis:
            await message.add_reaction(emoji)

    @app_commands.command(name="annonce", description="Publier une annonce dans le salon des annonces")
    @app_commands.describe(
        titre="Le titre de l'annonce",
        message="Le texte (utilise \\n pour aller à la ligne)",
        mention="Rôle à mentionner (optionnel)",
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def annonce(
        self, interaction: discord.Interaction, titre: str, message: str, mention: discord.Role | None = None
    ) -> None:
        assert interaction.guild
        channel = self.bot.cfg.channel(interaction.guild, "announcements") or interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Salon des annonces introuvable.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"📢 {titre}",
            description=message.replace("\\n", "\n"),
            colour=discord.Colour.gold(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"Publié par {interaction.user.display_name}")
        sent = await channel.send(
            content=mention.mention if mention else None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(roles=True, everyone=True),
        )
        if channel.is_news():
            try:
                await sent.publish()
            except discord.HTTPException:
                pass
        await interaction.response.send_message(f"✅ Annonce publiée dans {channel.mention}", ephemeral=True)

    @app_commands.command(name="setup", description="(Ré)appliquer la structure du serveur (config/server.yaml)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def setup_command(self, interaction: discord.Interaction) -> None:
        assert interaction.guild
        await interaction.response.defer(ephemeral=True, thinking=True)
        lines: list[str] = []
        try:
            await apply_structure(interaction.guild, self.bot.cfg, report=lines.append)
        except SetupError as exc:
            lines.append(f"❌ {exc}")
        except discord.HTTPException as exc:
            lines.append(f"❌ Erreur Discord : {exc}")
        text = "\n".join(lines)
        if len(text) > 1900:
            text = "…\n" + text[-1900:]
        await interaction.followup.send(text or "Rien à faire.", ephemeral=True)


async def setup(bot: CommunityBot) -> None:
    await bot.add_cog(Utility(bot))
