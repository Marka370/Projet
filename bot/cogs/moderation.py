"""Commandes slash de modération."""

from __future__ import annotations

from datetime import timedelta
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from ..client import CommunityBot
from ..setup_server import channel_overwrites_from_config
from ..utils import MAX_TIMEOUT, can_act_on, format_duration, parse_duration, send_log


def _ephemeral_error(message: str) -> dict:
    return {"content": f"❌ {message}", "ephemeral": True}


class Moderation(commands.Cog):
    def __init__(self, bot: CommunityBot):
        self.bot = bot

    # ------------------------------------------------------------------ helpers

    async def _log_sanction(
        self,
        interaction: discord.Interaction,
        action: str,
        target: discord.abc.User,
        reason: str,
        colour: discord.Colour,
        extra: Optional[str] = None,
    ) -> None:
        assert interaction.guild
        embed = discord.Embed(title=action, colour=colour, timestamp=discord.utils.utcnow())
        embed.add_field(name="Membre", value=f"{target.mention} ({target})", inline=False)
        embed.add_field(name="Modérateur", value=interaction.user.mention, inline=True)
        embed.add_field(name="Raison", value=reason[:1024], inline=True)
        if extra:
            embed.add_field(name="Détails", value=extra, inline=False)
        embed.set_footer(text=f"ID : {target.id}")
        await send_log(self.bot, interaction.guild, embed, channel_key="sanctions")

    async def _dm(self, user: discord.abc.User, guild: discord.Guild, text: str) -> None:
        try:
            await user.send(f"**{guild.name}** — {text}")
        except discord.HTTPException:
            pass  # MP fermés

    def _check_target(self, interaction: discord.Interaction, target: discord.Member) -> Optional[str]:
        assert isinstance(interaction.user, discord.Member)
        return can_act_on(interaction.user, target)

    # ------------------------------------------------------------------ avertissements

    @app_commands.command(name="warn", description="Avertir un membre")
    @app_commands.describe(membre="Le membre à avertir", raison="La raison de l'avertissement")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str) -> None:
        assert interaction.guild
        if error := self._check_target(interaction, membre):
            await interaction.response.send_message(**_ephemeral_error(error))
            return
        db = self.bot.db
        warning_id = db.add_warning(interaction.guild.id, membre.id, interaction.user.id, raison)
        count = db.count_warnings(interaction.guild.id, membre.id)
        await self._dm(membre, interaction.guild, f"⚠️ Tu as reçu un avertissement : {raison} ({count} au total)")

        extra = f"Avertissement n°{warning_id} — total : {count}"
        thresholds = {int(k): int(v) for k, v in (self.bot.cfg.bot.get("warn_thresholds") or {}).items()}
        sanction = ""
        if count in thresholds:
            duration = min(timedelta(minutes=thresholds[count]), MAX_TIMEOUT)
            try:
                await membre.timeout(duration, reason=f"{count} avertissements")
                sanction = f"\n🔇 Sanction automatique : mute {format_duration(duration)} ({count} avertissements)."
                extra += sanction
            except discord.HTTPException:
                pass

        await interaction.response.send_message(
            f"⚠️ {membre.mention} a été averti(e) : **{raison}** ({count} avertissement(s)).{sanction}"
        )
        await self._log_sanction(interaction, "⚠️ Avertissement", membre, raison, discord.Colour.gold(), extra)

    @app_commands.command(name="warns", description="Voir les avertissements d'un membre")
    @app_commands.describe(membre="Le membre concerné")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def warns(self, interaction: discord.Interaction, membre: discord.Member) -> None:
        assert interaction.guild
        warnings = self.bot.db.list_warnings(interaction.guild.id, membre.id)
        if not warnings:
            await interaction.response.send_message(f"✅ {membre.mention} n'a aucun avertissement.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"Avertissements de {membre.display_name} ({len(warnings)})",
            colour=discord.Colour.gold(),
        )
        for w in warnings[-25:]:
            embed.add_field(
                name=f"n°{w.id} — <t:{w.created_at}:d>",
                value=f"{w.reason[:200]}\npar <@{w.moderator_id}>",
                inline=False,
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unwarn", description="Retirer un avertissement (par son numéro)")
    @app_commands.describe(numero="Le numéro de l'avertissement (voir /warns)")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def unwarn(self, interaction: discord.Interaction, numero: int) -> None:
        assert interaction.guild
        if self.bot.db.delete_warning(interaction.guild.id, numero):
            await interaction.response.send_message(f"✅ Avertissement n°{numero} retiré.", ephemeral=True)
        else:
            await interaction.response.send_message(**_ephemeral_error(f"Avertissement n°{numero} introuvable."))

    @app_commands.command(name="clearwarns", description="Effacer tous les avertissements d'un membre")
    @app_commands.describe(membre="Le membre concerné")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def clearwarns(self, interaction: discord.Interaction, membre: discord.Member) -> None:
        assert interaction.guild
        removed = self.bot.db.clear_warnings(interaction.guild.id, membre.id)
        await interaction.response.send_message(
            f"✅ {removed} avertissement(s) effacé(s) pour {membre.mention}.", ephemeral=True
        )

    # ------------------------------------------------------------------ mute

    @app_commands.command(name="mute", description="Rendre un membre muet temporairement")
    @app_commands.describe(
        membre="Le membre à rendre muet",
        duree="Durée : 30s, 10m, 2h, 1j, 1h30m… (28 jours max)",
        raison="La raison",
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def mute(
        self, interaction: discord.Interaction, membre: discord.Member, duree: str, raison: str = "Aucune raison"
    ) -> None:
        assert interaction.guild
        if error := self._check_target(interaction, membre):
            await interaction.response.send_message(**_ephemeral_error(error))
            return
        duration = parse_duration(duree)
        if duration is None:
            await interaction.response.send_message(**_ephemeral_error("Durée invalide. Exemples : 10m, 2h, 1j."))
            return
        duration = min(duration, MAX_TIMEOUT)
        await membre.timeout(duration, reason=f"{interaction.user} : {raison}")
        await self._dm(membre, interaction.guild, f"🔇 Tu as été rendu muet pour {format_duration(duration)} : {raison}")
        await interaction.response.send_message(
            f"🔇 {membre.mention} est muet pour **{format_duration(duration)}** : {raison}"
        )
        await self._log_sanction(
            interaction, "🔇 Mute", membre, raison, discord.Colour.orange(), f"Durée : {format_duration(duration)}"
        )

    @app_commands.command(name="unmute", description="Rendre la parole à un membre")
    @app_commands.describe(membre="Le membre")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member) -> None:
        if not membre.is_timed_out():
            await interaction.response.send_message(**_ephemeral_error("Ce membre n'est pas muet."))
            return
        await membre.timeout(None, reason=f"Unmute par {interaction.user}")
        await interaction.response.send_message(f"🔊 {membre.mention} peut de nouveau parler.")
        await self._log_sanction(interaction, "🔊 Unmute", membre, "—", discord.Colour.green())

    # ------------------------------------------------------------------ kick / ban

    @app_commands.command(name="kick", description="Expulser un membre du serveur")
    @app_commands.describe(membre="Le membre à expulser", raison="La raison")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison") -> None:
        assert interaction.guild
        if error := self._check_target(interaction, membre):
            await interaction.response.send_message(**_ephemeral_error(error))
            return
        await self._dm(membre, interaction.guild, f"👢 Tu as été expulsé(e) : {raison}")
        await membre.kick(reason=f"{interaction.user} : {raison}")
        await interaction.response.send_message(f"👢 {membre} a été expulsé(e) : {raison}")
        await self._log_sanction(interaction, "👢 Expulsion", membre, raison, discord.Colour.dark_orange())

    @app_commands.command(name="ban", description="Bannir un membre du serveur")
    @app_commands.describe(
        membre="Le membre à bannir",
        raison="La raison",
        supprimer_messages="Supprimer ses messages des X derniers jours (0 à 7)",
    )
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        raison: str = "Aucune raison",
        supprimer_messages: app_commands.Range[int, 0, 7] = 0,
    ) -> None:
        assert interaction.guild
        if error := self._check_target(interaction, membre):
            await interaction.response.send_message(**_ephemeral_error(error))
            return
        await self._dm(membre, interaction.guild, f"🔨 Tu as été banni(e) : {raison}")
        await membre.ban(
            reason=f"{interaction.user} : {raison}", delete_message_seconds=supprimer_messages * 86400
        )
        await interaction.response.send_message(f"🔨 {membre} a été banni(e) : {raison}")
        await self._log_sanction(interaction, "🔨 Bannissement", membre, raison, discord.Colour.dark_red())

    @app_commands.command(name="unban", description="Débannir un utilisateur (par son ID)")
    @app_commands.describe(utilisateur_id="L'identifiant de l'utilisateur", raison="La raison")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def unban(self, interaction: discord.Interaction, utilisateur_id: str, raison: str = "Aucune raison") -> None:
        assert interaction.guild
        if not utilisateur_id.strip().isdigit():
            await interaction.response.send_message(**_ephemeral_error("L'ID doit être un nombre."))
            return
        user = discord.Object(id=int(utilisateur_id))
        try:
            await interaction.guild.unban(user, reason=f"{interaction.user} : {raison}")
        except discord.NotFound:
            await interaction.response.send_message(**_ephemeral_error("Cet utilisateur n'est pas banni."))
            return
        target = await self.bot.fetch_user(user.id)
        await interaction.response.send_message(f"✅ {target} a été débanni(e).")
        await self._log_sanction(interaction, "✅ Débannissement", target, raison, discord.Colour.green())

    # ------------------------------------------------------------------ salons

    @app_commands.command(name="clear", description="Supprimer des messages dans ce salon")
    @app_commands.describe(nombre="Nombre de messages à supprimer (1 à 100)", membre="Seulement les messages de ce membre")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def clear(
        self,
        interaction: discord.Interaction,
        nombre: app_commands.Range[int, 1, 100],
        membre: Optional[discord.Member] = None,
    ) -> None:
        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
            await interaction.response.send_message(**_ephemeral_error("Impossible ici."))
            return
        await interaction.response.defer(ephemeral=True)
        check = (lambda m: m.author.id == membre.id) if membre else (lambda m: True)
        deleted = await channel.purge(limit=nombre if not membre else 200, check=check, bulk=True)
        if membre:
            deleted = deleted[:nombre]
        await interaction.followup.send(f"🧹 {len(deleted)} message(s) supprimé(s).", ephemeral=True)
        embed = discord.Embed(
            description=f"🧹 {interaction.user.mention} a supprimé {len(deleted)} message(s) dans {channel.mention}",
            colour=discord.Colour.blue(),
        )
        assert interaction.guild
        await send_log(self.bot, interaction.guild, embed)

    @app_commands.command(name="slowmode", description="Régler le mode lent de ce salon")
    @app_commands.describe(secondes="Délai entre deux messages (0 pour désactiver, 21600 max)")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def slowmode(self, interaction: discord.Interaction, secondes: app_commands.Range[int, 0, 21600]) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(**_ephemeral_error("Uniquement dans un salon textuel."))
            return
        await channel.edit(slowmode_delay=secondes)
        text = "désactivé" if secondes == 0 else f"réglé à {secondes} s"
        await interaction.response.send_message(f"🐢 Mode lent {text}.")

    async def _set_locked(self, interaction: discord.Interaction, locked: bool, raison: str) -> None:
        channel = interaction.channel
        assert interaction.guild
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(**_ephemeral_error("Uniquement dans un salon textuel."))
            return
        targets = [interaction.guild.default_role]
        member_role = self.bot.cfg.role(interaction.guild, "member")
        if member_role is not None:
            targets.append(member_role)
        # Au déverrouillage, on revient aux permissions prévues par config/server.yaml.
        configured = channel_overwrites_from_config(interaction.guild, self.bot.cfg, channel)
        for target in targets:
            overwrite = channel.overwrites_for(target)
            if locked:
                overwrite.update(send_messages=False, send_messages_in_threads=False, add_reactions=False)
            else:
                original = configured.get(target, discord.PermissionOverwrite())
                overwrite.update(
                    send_messages=original.send_messages,
                    send_messages_in_threads=original.send_messages_in_threads,
                    add_reactions=original.add_reactions,
                )
            await channel.set_permissions(target, overwrite=overwrite, reason=f"{interaction.user} : {raison}")
        if locked:
            await interaction.response.send_message(f"🔒 Salon verrouillé : {raison}")
        else:
            await interaction.response.send_message("🔓 Salon déverrouillé.")

    @app_commands.command(name="lock", description="Verrouiller ce salon (plus personne ne peut écrire)")
    @app_commands.describe(raison="La raison")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def lock(self, interaction: discord.Interaction, raison: str = "Aucune raison") -> None:
        await self._set_locked(interaction, True, raison)

    @app_commands.command(name="unlock", description="Déverrouiller ce salon")
    @app_commands.default_permissions(manage_channels=True)
    @app_commands.guild_only()
    async def unlock(self, interaction: discord.Interaction) -> None:
        await self._set_locked(interaction, False, "—")

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        original = getattr(error, "original", error)
        if isinstance(original, discord.Forbidden):
            message = "Je n'ai pas la permission de faire ça (vérifie que mon rôle est assez haut)."
        else:
            message = f"Une erreur est survenue : {original}"
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)


async def setup(bot: CommunityBot) -> None:
    await bot.add_cog(Moderation(bot))
