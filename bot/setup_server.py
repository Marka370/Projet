"""Applique config/server.yaml à un serveur Discord.

Le script est idempotent : on peut le relancer autant de fois que voulu,
il crée ce qui manque et met à jour ce qui existe déjà (repéré par le nom).
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional

import discord

from .config import Config, find_channel
from .utils import colour
from .views import PANEL_VIEWS

Report = Callable[[str], None]


class SetupError(Exception):
    pass


def build_permissions(names: list[str] | None) -> discord.Permissions:
    perms = discord.Permissions.none()
    for name in names or []:
        setattr(perms, name, True)
    return perms


def build_overwrites(
    guild: discord.Guild, cfg: Config, spec: dict[str, Any] | None
) -> dict[Any, discord.PermissionOverwrite]:
    overwrites: dict[Any, discord.PermissionOverwrite] = {}
    for target_key, rule in (spec or {}).items():
        target = guild.default_role if target_key == "everyone" else cfg.role(guild, target_key)
        if target is None:
            continue
        overwrite = discord.PermissionOverwrite()
        for name in rule.get("allow") or []:
            setattr(overwrite, name, True)
        for name in rule.get("deny") or []:
            setattr(overwrite, name, False)
        overwrites[target] = overwrite
    return overwrites


def merge_overwrite_specs(*specs: dict[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for spec in specs:
        merged.update(spec or {})
    return merged


def channel_overwrites_from_config(
    guild: discord.Guild, cfg: Config, channel: discord.abc.GuildChannel
) -> dict[Any, discord.PermissionOverwrite]:
    """Permissions prévues par la config pour un salon existant (vide si non géré)."""
    for cat_spec, spec in cfg.iter_channels():
        if find_channel(guild, spec["name"], spec.get("type", "text")) == channel:
            merged = merge_overwrite_specs(cat_spec.get("permissions"), spec.get("permissions"))
            return build_overwrites(guild, cfg, merged)
    return {}


def _same_overwrites(
    current: dict[Any, discord.PermissionOverwrite], wanted: dict[Any, discord.PermissionOverwrite]
) -> bool:
    def ids(d: dict[Any, discord.PermissionOverwrite]) -> dict[int, tuple]:
        return {t.id: tuple(o.pair()) for t, o in d.items() if not o.is_empty()}

    return ids(current) == ids(wanted)


async def _wait_for_cache(check: Callable[[], bool], timeout: float = 15.0) -> None:
    """Attend que le cache de discord.py reflète les objets créés via l'API."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not check() and loop.time() < deadline:
        await asyncio.sleep(0.5)


async def apply_roles(guild: discord.Guild, cfg: Config, report: Report) -> None:
    for spec in cfg.roles:
        wanted = {
            "permissions": build_permissions(spec.get("permissions")),
            "colour": colour(spec.get("color"), discord.Colour.default()),
            "hoist": bool(spec.get("hoist", False)),
            "mentionable": bool(spec.get("mentionable", False)),
        }
        role = discord.utils.get(guild.roles, name=spec["name"])
        if role is None:
            await guild.create_role(name=spec["name"], reason="Mise en place du serveur", **wanted)
            report(f"➕ Rôle créé : {spec['name']}")
            continue
        if role >= guild.me.top_role:
            report(f"⚠️ Rôle {spec['name']} au-dessus du bot : non modifié")
            continue
        if (role.permissions, role.colour, role.hoist, role.mentionable) != tuple(wanted.values()):
            await role.edit(reason="Mise en place du serveur", **wanted)
            report(f"✏️ Rôle mis à jour : {spec['name']}")

    await _wait_for_cache(lambda: all(cfg.role(guild, spec["key"]) for spec in cfg.roles))

    # Ordre : juste en dessous du rôle du bot, dans l'ordre du fichier.
    # On relit les rôles via l'API : les positions en cache sont faussées par les créations.
    fresh = {r.id: r for r in await guild.fetch_roles()}
    bot_top = max(fresh[r.id].position for r in guild.me.roles if r.id in fresh)
    movable = []
    for spec in cfg.roles:
        cached = cfg.role(guild, spec["key"])
        role = fresh.get(cached.id) if cached else None
        if role is not None and role.position < bot_top:
            movable.append(role)
    positions = {role: max(bot_top - 1 - i, 1) for i, role in enumerate(movable)}
    if any(role.position != pos for role, pos in positions.items()):
        try:
            await guild.edit_role_positions(positions, reason="Mise en place du serveur")
            report("↕️ Rôles réordonnés")
        except discord.HTTPException as exc:
            report(f"⚠️ Impossible de réordonner les rôles : {exc}")


async def _create_channel(
    guild: discord.Guild,
    spec: dict[str, Any],
    category: discord.CategoryChannel,
    overwrites: dict[Any, discord.PermissionOverwrite],
    report: Report,
) -> discord.abc.GuildChannel:
    ctype = spec.get("type", "text")
    common = {"category": category, "overwrites": overwrites, "reason": "Mise en place du serveur"}
    if ctype == "voice":
        return await guild.create_voice_channel(
            spec["name"], user_limit=spec.get("user_limit", 0), **common
        )
    text_options = {"topic": spec.get("topic") or "", "slowmode_delay": spec.get("slowmode", 0)}
    if ctype == "forum":
        try:
            return await guild.create_forum(spec["name"], **text_options, **common)
        except discord.HTTPException:
            report(f"ℹ️ Forum indisponible pour {spec['name']} : salon textuel créé à la place")
    if ctype == "news":
        try:
            return await guild.create_text_channel(spec["name"], news=True, **text_options, **common)
        except discord.HTTPException:
            report(
                f"ℹ️ {spec['name']} créé en salon textuel : active la « Communauté » dans les "
                "paramètres du serveur pour en faire un salon d'annonces"
            )
    return await guild.create_text_channel(spec["name"], **text_options, **common)


async def apply_channels(guild: discord.Guild, cfg: Config, report: Report) -> None:
    for cat_index, cat_spec in enumerate(cfg.categories):
        cat_overwrites = build_overwrites(guild, cfg, cat_spec.get("permissions"))
        category = discord.utils.get(guild.categories, name=cat_spec["name"])
        if category is None:
            category = await guild.create_category(
                cat_spec["name"], overwrites=cat_overwrites, reason="Mise en place du serveur"
            )
            report(f"➕ Catégorie créée : {cat_spec['name']}")
        elif not _same_overwrites(category.overwrites, cat_overwrites):
            await category.edit(overwrites=cat_overwrites, reason="Mise en place du serveur")
            report(f"✏️ Permissions mises à jour : {cat_spec['name']}")
        if category.position != cat_index:
            try:
                await category.edit(position=cat_index)
            except discord.HTTPException:
                pass

        for ch_index, spec in enumerate(cat_spec.get("channels") or []):
            merged = merge_overwrite_specs(cat_spec.get("permissions"), spec.get("permissions"))
            overwrites = build_overwrites(guild, cfg, merged)
            channel = find_channel(guild, spec["name"], spec.get("type", "text"))
            if channel is None:
                await _create_channel(guild, spec, category, overwrites, report)
                report(f"   ➕ Salon créé : {spec['name']}")
                continue

            changes: dict[str, Any] = {}
            if channel.category != category:
                changes["category"] = category
            if not _same_overwrites(channel.overwrites, overwrites):
                changes["overwrites"] = overwrites
            if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                if (channel.topic or "") != (spec.get("topic") or ""):
                    changes["topic"] = spec.get("topic") or ""
                if channel.slowmode_delay != spec.get("slowmode", 0):
                    changes["slowmode_delay"] = spec.get("slowmode", 0)
            if (
                spec.get("type") == "news"
                and isinstance(channel, discord.TextChannel)
                and not channel.is_news()
                and "COMMUNITY" in getattr(guild, "features", [])
            ):
                changes["type"] = discord.ChannelType.news
            if isinstance(channel, discord.VoiceChannel):
                if channel.user_limit != spec.get("user_limit", 0):
                    changes["user_limit"] = spec.get("user_limit", 0)
            if changes:
                try:
                    await channel.edit(reason="Mise en place du serveur", **changes)
                    report(f"   ✏️ Salon mis à jour : {spec['name']}")
                except discord.HTTPException as exc:
                    report(f"   ⚠️ {spec['name']} non mis à jour : {exc}")

    await _wait_for_cache(lambda: all(cfg.channel(guild, ch["key"]) for _, ch in cfg.iter_channels()))


async def remove_default_channels(guild: discord.Guild, cfg: Config, report: Report) -> None:
    names = set(cfg.server.get("remove_default_channels") or [])
    managed = {c["name"] for c in cfg.categories} | {ch["name"] for _, ch in cfg.iter_channels()}
    names -= managed
    if not names:
        return

    async def delete(channel: discord.abc.GuildChannel) -> bool:
        try:
            await channel.delete(reason="Nettoyage des salons par défaut")
            report(f"🗑️ Salon par défaut supprimé : {channel.name}")
            return True
        except discord.HTTPException as exc:
            report(f"⚠️ Impossible de supprimer {channel.name} : {exc}")
            return False

    deleted: set[int] = set()
    for channel in list(guild.channels):
        if not isinstance(channel, discord.CategoryChannel) and channel.name in names:
            if await delete(channel):
                deleted.add(channel.id)
    # Une catégorie par défaut n'est supprimée que si elle est (devenue) vide.
    for category in list(guild.categories):
        if category.name in names and all(c.id in deleted for c in category.channels):
            await delete(category)


async def apply_server_settings(guild: discord.Guild, cfg: Config, report: Report) -> None:
    server = cfg.server
    changes: dict[str, Any] = {}
    if server.get("verification_level"):
        value = discord.VerificationLevel[server["verification_level"]]
        if guild.verification_level != value:
            changes["verification_level"] = value
    if server.get("explicit_content_filter"):
        value = discord.ContentFilter[server["explicit_content_filter"]]
        if guild.explicit_content_filter != value:
            changes["explicit_content_filter"] = value
    if server.get("default_notifications"):
        value = discord.NotificationLevel[server["default_notifications"]]
        if guild.default_notifications != value:
            changes["default_notifications"] = value
    if server.get("afk_channel"):
        afk = cfg.channel(guild, server["afk_channel"])
        if isinstance(afk, discord.VoiceChannel) and guild.afk_channel != afk:
            changes["afk_channel"] = afk
    if server.get("afk_timeout") and guild.afk_timeout != server["afk_timeout"]:
        changes["afk_timeout"] = server["afk_timeout"]
    if changes:
        try:
            await guild.edit(reason="Mise en place du serveur", **changes)
            report(f"⚙️ Réglages du serveur mis à jour : {', '.join(changes)}")
        except discord.HTTPException as exc:
            report(f"⚠️ Réglages du serveur non appliqués : {exc}")


async def _find_bot_message(
    channel: discord.TextChannel, title: str
) -> Optional[discord.Message]:
    async for message in channel.history(limit=50):
        if message.author == channel.guild.me and message.embeds and message.embeds[0].title == title:
            return message
    return None


async def apply_messages(guild: discord.Guild, cfg: Config, report: Report) -> None:
    for _, spec in cfg.iter_channels():
        message_spec = spec.get("message")
        if not message_spec:
            continue
        channel = cfg.channel(guild, spec["key"])
        if not isinstance(channel, discord.TextChannel):
            continue
        embed = discord.Embed(
            title=message_spec["title"],
            description=(message_spec.get("description") or "").strip(),
            colour=colour(message_spec.get("color")),
        )
        panel = spec.get("panel")
        view = PANEL_VIEWS[panel](cfg) if panel else None
        existing = await _find_bot_message(channel, message_spec["title"])
        if existing is None:
            if view is not None:
                await channel.send(embed=embed, view=view)
            else:
                await channel.send(embed=embed)
            report(f"💬 Message publié dans {spec['name']}")
            continue
        old = existing.embeds[0]
        if old.description != embed.description or old.colour != embed.colour or view is not None:
            await existing.edit(embed=embed, view=view)
            report(f"💬 Message mis à jour dans {spec['name']}")


async def apply_structure(guild: discord.Guild, cfg: Config, report: Report = print) -> None:
    if not guild.me.guild_permissions.administrator:
        raise SetupError(
            "Le bot doit avoir la permission Administrateur pour configurer le serveur. "
            "Ré-invite-le avec le lien du README (permissions=8)."
        )
    report(f"🚀 Configuration de « {guild.name} »…")
    await apply_roles(guild, cfg, report)
    await apply_channels(guild, cfg, report)
    await remove_default_channels(guild, cfg, report)
    await apply_server_settings(guild, cfg, report)
    await apply_messages(guild, cfg, report)
    report("✅ Serveur configuré !")
