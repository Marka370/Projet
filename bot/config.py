"""Chargement et validation de config/server.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterator, Optional

import discord
import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = ROOT / "config" / "server.yaml"

CHANNEL_TYPES = {"text", "news", "forum", "voice"}
TEXT_LIKE = {"text", "news", "forum"}

# Salons et rôles dont le bot a besoin pour fonctionner.
REQUIRED_CHANNELS = {"welcome", "rules", "verification", "roles", "tickets", "logs", "sanctions"}
REQUIRED_CATEGORIES = {"support"}
REQUIRED_ROLES = {"member"}
PANELS = {"verification", "roles", "tickets"}


class Config:
    """Accès pratique à la configuration du serveur."""

    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.server: dict[str, Any] = data.get("server") or {}
        self.bot: dict[str, Any] = data.get("bot") or {}
        self.roles: list[dict[str, Any]] = data.get("roles") or []
        self.categories: list[dict[str, Any]] = data.get("categories") or []
        self._roles = {r["key"]: r for r in self.roles}
        self._categories = {c["key"]: c for c in self.categories}
        self._channels = {ch["key"]: ch for _, ch in self.iter_channels()}

    @classmethod
    def load(cls, path: Optional[str | Path] = None) -> "Config":
        path = Path(path or os.getenv("SERVER_CONFIG") or DEFAULT_CONFIG_PATH)
        with open(path, encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {})

    def iter_channels(self) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
        for category in self.categories:
            for channel in category.get("channels") or []:
                yield category, channel

    # --- Résolution des objets Discord à partir des keys ---

    def role(self, guild: discord.Guild, key: str) -> Optional[discord.Role]:
        spec = self._roles.get(key)
        return discord.utils.get(guild.roles, name=spec["name"]) if spec else None

    def channel(self, guild: discord.Guild, key: str) -> Optional[discord.abc.GuildChannel]:
        spec = self._channels.get(key)
        if not spec:
            return None
        return find_channel(guild, spec["name"], spec.get("type", "text"))

    def category(self, guild: discord.Guild, key: str) -> Optional[discord.CategoryChannel]:
        spec = self._categories.get(key)
        return discord.utils.get(guild.categories, name=spec["name"]) if spec else None

    def staff_roles(self, guild: discord.Guild) -> list[discord.Role]:
        roles = [self.role(guild, r["key"]) for r in self.roles if r.get("staff")]
        return [r for r in roles if r is not None]

    def self_roles(self) -> list[dict[str, Any]]:
        return [r for r in self.roles if r.get("self_role")]

    def role_spec(self, key: str) -> Optional[dict[str, Any]]:
        return self._roles.get(key)


def normalize_text_name(name: str) -> str:
    """Discord met les noms de salons textuels en minuscules et remplace les espaces."""
    return "-".join(name.lower().split())


def find_channel(guild: discord.Guild, name: str, ctype: str) -> Optional[discord.abc.GuildChannel]:
    if ctype == "voice":
        return discord.utils.find(
            lambda c: isinstance(c, discord.VoiceChannel) and c.name == name, guild.channels
        )
    wanted = normalize_text_name(name)
    return discord.utils.find(
        lambda c: isinstance(c, (discord.TextChannel, discord.ForumChannel)) and c.name == wanted,
        guild.channels,
    )


def is_staff(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return perms.administrator or perms.manage_messages or perms.moderate_members


def validate(data: dict[str, Any]) -> list[str]:
    """Retourne la liste des erreurs trouvées dans la configuration."""
    errors: list[str] = []
    valid_perms = set(discord.Permissions.VALID_FLAGS)

    def check_perms(where: str, perms: Any) -> None:
        if perms is None:
            return
        if not isinstance(perms, list):
            errors.append(f"{where}: doit être une liste")
            return
        for p in perms:
            if p not in valid_perms:
                errors.append(f"{where}: permission inconnue « {p} »")

    roles = data.get("roles") or []
    role_keys: set[str] = set()
    role_names: set[str] = set()
    for i, role in enumerate(roles):
        key, name = role.get("key"), role.get("name")
        if not key or not name:
            errors.append(f"roles[{i}]: « key » et « name » sont obligatoires")
            continue
        if key in role_keys:
            errors.append(f"rôle « {key} »: key en double")
        if name in role_names:
            errors.append(f"rôle « {key} »: nom en double")
        role_keys.add(key)
        role_names.add(name)
        check_perms(f"rôle « {key} »", role.get("permissions"))
        color = role.get("color")
        if color is not None:
            try:
                discord.Colour.from_str(str(color))
            except ValueError:
                errors.append(f"rôle « {key} »: couleur invalide « {color} »")

    def check_overwrites(where: str, overwrites: Any) -> None:
        if overwrites is None:
            return
        if not isinstance(overwrites, dict):
            errors.append(f"{where}: « permissions » doit être un dictionnaire")
            return
        for target, rule in overwrites.items():
            if target != "everyone" and target not in role_keys:
                errors.append(f"{where}: cible inconnue « {target} » (ni « everyone » ni une key de rôle)")
            if not isinstance(rule, dict):
                errors.append(f"{where}/{target}: doit contenir allow et/ou deny")
                continue
            unknown = set(rule) - {"allow", "deny"}
            if unknown:
                errors.append(f"{where}/{target}: champs inconnus {sorted(unknown)}")
            check_perms(f"{where}/{target}/allow", rule.get("allow"))
            check_perms(f"{where}/{target}/deny", rule.get("deny"))

    category_keys: set[str] = set()
    channel_keys: set[str] = set()
    channel_types: dict[str, str] = {}
    names_by_type: dict[str, set[str]] = {"text": set(), "voice": set()}
    for category in data.get("categories") or []:
        ckey = category.get("key")
        if not ckey or not category.get("name"):
            errors.append("catégorie sans « key » ou « name »")
            continue
        if ckey in category_keys:
            errors.append(f"catégorie « {ckey} »: key en double")
        category_keys.add(ckey)
        check_overwrites(f"catégorie « {ckey} »", category.get("permissions"))

        for channel in category.get("channels") or []:
            key, name = channel.get("key"), channel.get("name")
            ctype = channel.get("type", "text")
            if not key or not name:
                errors.append(f"catégorie « {ckey} »: salon sans « key » ou « name »")
                continue
            where = f"salon « {key} »"
            if key in channel_keys:
                errors.append(f"{where}: key en double")
            channel_keys.add(key)
            channel_types[key] = ctype
            if ctype not in CHANNEL_TYPES:
                errors.append(f"{where}: type inconnu « {ctype} » ({', '.join(sorted(CHANNEL_TYPES))})")
                continue
            if ctype in TEXT_LIKE and normalize_text_name(name) != name:
                errors.append(f"{where}: un nom de salon textuel doit être en minuscules et sans espace")
            bucket = "voice" if ctype == "voice" else "text"
            if name in names_by_type[bucket]:
                errors.append(f"{where}: nom en double « {name} »")
            names_by_type[bucket].add(name)
            check_overwrites(where, channel.get("permissions"))
            panel = channel.get("panel")
            if panel is not None:
                if panel not in PANELS:
                    errors.append(f"{where}: panneau inconnu « {panel} »")
                if not channel.get("message"):
                    errors.append(f"{where}: un panneau a besoin d'un « message »")
            if channel.get("message") and ctype == "voice":
                errors.append(f"{where}: impossible de poster un message dans un salon vocal")
            if channel.get("message") and not channel["message"].get("title"):
                errors.append(f"{where}: le message doit avoir un « title »")

    for key in sorted(REQUIRED_CHANNELS - channel_keys):
        errors.append(f"salon obligatoire manquant: key « {key} »")
    for key in sorted(REQUIRED_CATEGORIES - category_keys):
        errors.append(f"catégorie obligatoire manquante: key « {key} »")
    for key in sorted(REQUIRED_ROLES - role_keys):
        errors.append(f"rôle obligatoire manquant: key « {key} »")
    for key in REQUIRED_CHANNELS & channel_keys:
        if channel_types[key] == "voice":
            errors.append(f"salon « {key} »: doit être un salon textuel")

    server = data.get("server") or {}
    enums = {
        "verification_level": discord.VerificationLevel,
        "explicit_content_filter": discord.ContentFilter,
        "default_notifications": discord.NotificationLevel,
    }
    for field, enum in enums.items():
        value = server.get(field)
        if value is not None and value not in enum.__members__:
            errors.append(f"server.{field}: valeur invalide « {value} » ({', '.join(enum.__members__)})")
    afk = server.get("afk_channel")
    if afk is not None and channel_types.get(afk) != "voice":
        errors.append(f"server.afk_channel: « {afk} » n'est pas la key d'un salon vocal")

    bot = data.get("bot") or {}
    for count, minutes in (bot.get("warn_thresholds") or {}).items():
        if not isinstance(count, int) or not isinstance(minutes, int) or minutes <= 0:
            errors.append(f"bot.warn_thresholds: entrée invalide {count}: {minutes}")
        elif minutes > 40320:
            errors.append(f"bot.warn_thresholds: {minutes} min dépasse le maximum Discord (28 jours)")

    return errors
