import copy

import discord

from bot.config import Config, normalize_text_name, validate
from bot.setup_server import build_overwrites, build_permissions, merge_overwrite_specs

CFG = Config.load()


def test_default_config_is_valid():
    assert validate(CFG.data) == []


def test_every_self_role_has_a_label():
    assert CFG.self_roles(), "au moins un rôle au choix attendu"
    for spec in CFG.self_roles():
        assert spec["self_role"].get("label")


def test_validate_reports_unknown_permission_and_target():
    data = copy.deepcopy(CFG.data)
    data["roles"][0]["permissions"] = ["voler_la_lune"]
    data["categories"][0]["permissions"] = {"inconnu": {"allow": ["view_channel"]}}
    errors = validate(data)
    assert any("voler_la_lune" in e for e in errors)
    assert any("inconnu" in e for e in errors)


def test_validate_reports_missing_required_channel_and_bad_name():
    data = copy.deepcopy(CFG.data)
    for category in data["categories"]:
        category["channels"] = [c for c in category.get("channels", []) if c["key"] != "logs"]
    data["categories"][1]["channels"][0]["name"] = "Nom Avec Espaces"
    errors = validate(data)
    assert any("« logs »" in e for e in errors)
    assert any("minuscules" in e for e in errors)


def test_normalize_text_name():
    assert normalize_text_name("Salon Général") == "salon-général"


class FakeRole:
    def __init__(self, id, name):
        self.id, self.name = id, name

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, FakeRole) and other.id == self.id


class FakeGuild:
    def __init__(self, cfg):
        self.default_role = FakeRole(0, "@everyone")
        self.roles = [self.default_role] + [FakeRole(i + 1, r["name"]) for i, r in enumerate(cfg.roles)]


def test_channel_overwrites_merge_category_and_channel():
    guild = FakeGuild(CFG)
    category = next(c for c in CFG.categories if c["key"] == "accueil")
    channel = next(ch for ch in category["channels"] if ch["key"] == "verification")
    merged = merge_overwrite_specs(category.get("permissions"), channel.get("permissions"))
    overwrites = build_overwrites(guild, CFG, merged)

    everyone = overwrites[guild.default_role]
    assert everyone.view_channel is True and everyone.send_messages is False
    member = overwrites[CFG.role(guild, "member")]
    assert member.view_channel is False  # le salon disparaît une fois vérifié


def test_build_permissions():
    perms = build_permissions(["kick_members", "ban_members"])
    assert perms.kick_members and perms.ban_members and not perms.administrator
    assert build_permissions(None) == discord.Permissions.none()
