"""Boutons persistants : vérification, rôles au choix, tickets.

Les custom_id sont fixes : les boutons continuent de fonctionner
après un redémarrage du bot.
"""

from __future__ import annotations

import io
import re
from typing import TYPE_CHECKING, Any

import discord

from .config import Config
from .utils import send_log

if TYPE_CHECKING:
    from .client import CommunityBot


def _bot(interaction: discord.Interaction) -> "CommunityBot":
    return interaction.client  # type: ignore[return-value]


# --------------------------------------------------------------------- vérification


class VerificationView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="J'accepte le règlement",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="verify:accept",
    )
    async def accept(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        bot = _bot(interaction)
        member = interaction.user
        assert isinstance(member, discord.Member) and interaction.guild
        role = bot.cfg.role(interaction.guild, "member")
        if role is None:
            await interaction.response.send_message(
                "⚠️ Le rôle Membre est introuvable, préviens le staff.", ephemeral=True
            )
            return
        if role in member.roles:
            await interaction.response.send_message("Tu es déjà vérifié(e) 😉", ephemeral=True)
            return
        try:
            await member.add_roles(role, reason="Vérification (règlement accepté)")
        except discord.Forbidden:
            await interaction.response.send_message(
                "⚠️ Je n'ai pas la permission de te donner le rôle, préviens le staff.", ephemeral=True
            )
            return
        await interaction.response.send_message(
            "🎉 Bienvenue ! Tu as maintenant accès à tout le serveur. "
            "Passe dans le salon des rôles pour choisir tes notifications.",
            ephemeral=True,
        )
        embed = discord.Embed(
            description=f"✅ {member.mention} a accepté le règlement.", colour=discord.Colour.green()
        )
        await send_log(bot, interaction.guild, embed)


# --------------------------------------------------------------------- rôles au choix


class SelfRoleButton(discord.ui.Button):
    def __init__(self, key: str, spec: dict[str, Any]) -> None:
        options = spec["self_role"]
        super().__init__(
            label=options.get("label") or spec["name"],
            emoji=options.get("emoji"),
            style=discord.ButtonStyle.secondary,
            custom_id=f"selfrole:{key}",
        )
        self.key = key

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = _bot(interaction)
        member = interaction.user
        assert isinstance(member, discord.Member) and interaction.guild
        role = bot.cfg.role(interaction.guild, self.key)
        if role is None:
            await interaction.response.send_message("⚠️ Ce rôle n'existe plus.", ephemeral=True)
            return
        try:
            if role in member.roles:
                await member.remove_roles(role, reason="Rôle au choix retiré")
                message = f"➖ Rôle **{role.name}** retiré."
            else:
                await member.add_roles(role, reason="Rôle au choix ajouté")
                message = f"➕ Rôle **{role.name}** ajouté."
        except discord.Forbidden:
            message = "⚠️ Je n'ai pas la permission de gérer ce rôle."
        await interaction.response.send_message(message, ephemeral=True)


class SelfRolesView(discord.ui.View):
    def __init__(self, cfg: Config) -> None:
        super().__init__(timeout=None)
        for spec in cfg.self_roles()[:25]:
            self.add_item(SelfRoleButton(spec["key"], spec))


# --------------------------------------------------------------------- tickets


def _ticket_owner_id(channel: discord.abc.GuildChannel) -> int | None:
    topic = getattr(channel, "topic", None) or ""
    match = re.search(r"id:(\d+)", topic)
    return int(match.group(1)) if match else None


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "", name.lower().replace(" ", "-"))
    return slug[:20] or "membre"


class TicketOpenView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ouvrir un ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="ticket:open",
    )
    async def open_ticket(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        bot = _bot(interaction)
        guild = interaction.guild
        member = interaction.user
        assert guild and isinstance(member, discord.Member)
        category = bot.cfg.category(guild, "support")
        if category is None:
            await interaction.response.send_message(
                "⚠️ La catégorie support est introuvable, préviens le staff.", ephemeral=True
            )
            return
        for channel in category.text_channels:
            if _ticket_owner_id(channel) == member.id:
                await interaction.response.send_message(
                    f"Tu as déjà un ticket ouvert : {channel.mention}", ephemeral=True
                )
                return

        await interaction.response.defer(ephemeral=True, thinking=True)
        overwrites: dict[Any, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, attach_files=True,
                embed_links=True, read_message_history=True,
            ),
        }
        for role in bot.cfg.staff_roles(guild):
            overwrites[role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_messages=True
            )
        member_role = bot.cfg.role(guild, "member")
        if member_role is not None:
            overwrites[member_role] = discord.PermissionOverwrite(view_channel=False)

        channel = await guild.create_text_channel(
            f"ticket-{_slug(member.name)}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket de {member} | id:{member.id}",
            reason=f"Ticket ouvert par {member}",
        )
        staff_mentions = " ".join(r.mention for r in bot.cfg.staff_roles(guild)
                                  if not r.permissions.administrator)
        embed = discord.Embed(
            title="🎫 Ticket ouvert",
            description=(
                f"Salut {member.mention} ! Explique ta demande ici, un membre du staff va te répondre.\n"
                "Clique sur **Fermer le ticket** quand c'est réglé."
            ),
            colour=discord.Colour.blurple(),
        )
        await channel.send(
            content=f"{member.mention} {staff_mentions}".strip(),
            embed=embed,
            view=TicketCloseView(),
            allowed_mentions=discord.AllowedMentions(users=True, roles=True),
        )
        await interaction.followup.send(f"✅ Ton ticket est ouvert : {channel.mention}", ephemeral=True)
        await send_log(
            bot, guild,
            discord.Embed(description=f"🎫 Ticket {channel.mention} ouvert par {member.mention}",
                          colour=discord.Colour.blurple()),
        )


class TicketCloseView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fermer le ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close",
    )
    async def close_ticket(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await close_ticket(interaction)


async def close_ticket(interaction: discord.Interaction) -> None:
    bot = _bot(interaction)
    channel = interaction.channel
    member = interaction.user
    assert isinstance(member, discord.Member) and interaction.guild
    if not isinstance(channel, discord.TextChannel) or _ticket_owner_id(channel) is None:
        await interaction.response.send_message("Ce salon n'est pas un ticket.", ephemeral=True)
        return
    staff = set(bot.cfg.staff_roles(interaction.guild))
    is_owner = _ticket_owner_id(channel) == member.id
    if not (is_owner or staff.intersection(member.roles) or member.guild_permissions.administrator):
        await interaction.response.send_message("Tu ne peux pas fermer ce ticket.", ephemeral=True)
        return

    await interaction.response.send_message("🔒 Fermeture du ticket…")
    lines = []
    async for message in channel.history(limit=500, oldest_first=True):
        stamp = message.created_at.strftime("%d/%m/%Y %H:%M")
        text = message.clean_content or ("[embed]" if message.embeds else "")
        attachments = " ".join(a.url for a in message.attachments)
        lines.append(f"[{stamp}] {message.author}: {text} {attachments}".rstrip())
    transcript = discord.File(
        io.BytesIO("\n".join(lines).encode("utf-8")), filename=f"{channel.name}.txt"
    )
    embed = discord.Embed(
        description=f"🔒 Ticket **#{channel.name}** fermé par {member.mention}",
        colour=discord.Colour.dark_grey(),
    )
    await send_log(bot, interaction.guild, embed, file=transcript)
    await channel.delete(reason=f"Ticket fermé par {member}")


PANEL_VIEWS = {
    "verification": lambda cfg: VerificationView(),
    "roles": lambda cfg: SelfRolesView(cfg),
    "tickets": lambda cfg: TicketOpenView(),
}


def register_persistent_views(bot: "CommunityBot") -> None:
    bot.add_view(VerificationView())
    bot.add_view(SelfRolesView(bot.cfg))
    bot.add_view(TicketOpenView())
    bot.add_view(TicketCloseView())
