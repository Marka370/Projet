"""Test de bout en bout de apply_structure sur un faux serveur en mémoire."""

import asyncio
import itertools

import discord

from bot.config import Config
from bot.setup_server import apply_structure

CFG = Config.load()
_ids = itertools.count(1000)


class FakeRole:
    def __init__(self, guild, name, position, permissions=None, colour=None, hoist=False, mentionable=False):
        self.id = next(_ids)
        self.guild, self.name, self.position = guild, name, position
        self.permissions = permissions or discord.Permissions.none()
        self.colour = colour or discord.Colour.default()
        self.hoist, self.mentionable = hoist, mentionable

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, FakeRole) and other.id == self.id

    def __lt__(self, other):
        return self.position < other.position

    def __ge__(self, other):
        return self.position >= other.position

    async def edit(self, reason=None, **kwargs):
        self.guild.calls.append(("role.edit", self.name))
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakeMessage:
    def __init__(self, author, embed):
        self.author, self.embeds = author, [embed]

    async def edit(self, embed=None, view=None):
        self.embeds = [embed]


class _ChannelMixin:
    category = None
    overwrites = None

    def _init(self, guild, name, category, overwrites):
        self.id = next(_ids)
        self.guild, self.name, self.category = guild, name, category
        self.overwrites = dict(overwrites or {})
        self.position = len(guild.channels)
        guild.channels.append(self)

    async def edit(self, reason=None, **kwargs):
        self.guild.calls.append(("channel.edit", self.name, tuple(sorted(kwargs))))
        if "type" in kwargs:
            self._type = kwargs.pop("type").value
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def delete(self, reason=None):
        self.guild.calls.append(("channel.delete", self.name))
        self.guild.channels.remove(self)


class FakeCategory(_ChannelMixin, discord.CategoryChannel):
    channels = None

    def __init__(self, guild, name, overwrites=None):
        self._init(guild, name, None, overwrites)

    @property
    def channels(self):  # noqa: F811
        return [c for c in self.guild.channels if c.category is self]


class FakeText(_ChannelMixin, discord.TextChannel):
    def __init__(self, guild, name, category=None, overwrites=None, topic="", slowmode_delay=0, news=False):
        self._init(guild, "-".join(name.lower().split()), category, overwrites)
        self.topic, self.slowmode_delay = topic, slowmode_delay
        self._type = discord.ChannelType.news.value if news else discord.ChannelType.text.value
        self.messages = []

    def history(self, limit=50):
        async def gen():
            for message in reversed(self.messages[-limit:]):
                yield message
        return gen()

    async def send(self, embed=None, view=None):
        self.messages.append(FakeMessage(self.guild.me, embed))


class FakeVoice(_ChannelMixin, discord.VoiceChannel):
    def __init__(self, guild, name, category=None, overwrites=None, user_limit=0):
        self._init(guild, name, category, overwrites)
        self.user_limit = user_limit


class FakeResponse:
    status, reason = 400, "Bad Request"


class FakePerms:
    administrator = True


class FakeMember:
    guild_permissions = FakePerms()


class FakeGuild:
    def __init__(self):
        self.name = "Test"
        self.features = []
        self.calls = []
        self.channels = []
        self.default_role = FakeRole(self, "@everyone", 0)
        self.bot_role = FakeRole(self, "Bot", 1)
        self.roles = [self.default_role, self.bot_role]
        self.me = FakeMember()
        self.me.top_role = self.bot_role
        self.me.roles = [self.default_role, self.bot_role]
        self.verification_level = discord.VerificationLevel.none
        self.explicit_content_filter = discord.ContentFilter.disabled
        self.default_notifications = discord.NotificationLevel.all_messages
        self.afk_channel, self.afk_timeout = None, 300
        # Salons créés par défaut par Discord
        text = FakeCategory(self, "Salons textuels")
        FakeText(self, "général", category=text)
        voice = FakeCategory(self, "Salons vocaux")
        FakeVoice(self, "Général", category=voice)
        self.calls.clear()

    @property
    def categories(self):
        return [c for c in self.channels if isinstance(c, FakeCategory)]

    async def create_role(self, name, reason=None, **kwargs):
        self.calls.append(("create_role", name))
        for role in self.roles[1:]:
            role.position += 1
        role = FakeRole(self, name, 1, **kwargs)
        self.roles.append(role)
        return role

    async def fetch_roles(self):
        return list(self.roles)

    async def edit_role_positions(self, positions, reason=None):
        self.calls.append(("edit_role_positions",))
        for role, position in positions.items():
            role.position = position

    async def create_category(self, name, overwrites=None, reason=None):
        self.calls.append(("create_category", name))
        return FakeCategory(self, name, overwrites)

    async def create_text_channel(self, name, reason=None, **kwargs):
        self.calls.append(("create_text_channel", name))
        if kwargs.get("news") and "COMMUNITY" not in self.features:
            raise discord.HTTPException(FakeResponse(), "Communauté requise")
        return FakeText(self, name, **kwargs)

    async def create_forum(self, name, reason=None, **kwargs):
        return await self.create_text_channel(name, **kwargs)

    async def create_voice_channel(self, name, reason=None, **kwargs):
        self.calls.append(("create_voice_channel", name))
        return FakeVoice(self, name, **kwargs)

    async def edit(self, reason=None, **kwargs):
        self.calls.append(("guild.edit", tuple(sorted(kwargs))))
        for key, value in kwargs.items():
            setattr(self, key, value)


def run(guild):
    lines = []
    asyncio.run(apply_structure(guild, CFG, report=lines.append))
    return lines


def test_first_run_creates_everything():
    guild = FakeGuild()
    run(guild)

    for spec in CFG.roles:
        role = CFG.role(guild, spec["key"])
        assert role is not None, spec["name"]
        assert role < guild.bot_role
    order = [CFG.role(guild, spec["key"]).position for spec in CFG.roles]
    assert order == sorted(order, reverse=True), "les rôles suivent l'ordre du fichier"

    for category, spec in CFG.iter_channels():
        channel = CFG.channel(guild, spec["key"])
        assert channel is not None, spec["name"]
        assert channel.category is CFG.category(guild, category["key"])

    names = {c.name for c in guild.channels}
    assert "général" not in names and "Salons textuels" not in names, "salons par défaut supprimés"
    assert guild.afk_channel is CFG.channel(guild, "afk")
    assert guild.verification_level == discord.VerificationLevel.medium

    member = CFG.role(guild, "member")
    verification = CFG.channel(guild, "verification")
    assert verification.overwrites[guild.default_role].view_channel is True
    assert verification.overwrites[member].view_channel is False
    staff_chat = CFG.channel(guild, "staff_chat")
    assert staff_chat.overwrites[guild.default_role].view_channel is False

    for key in ("rules", "verification", "roles", "tickets"):
        assert len(CFG.channel(guild, key).messages) == 1, key


def test_second_run_changes_nothing():
    guild = FakeGuild()
    run(guild)
    guild.calls.clear()
    run(guild)
    structural = [c for c in guild.calls if c[0] != "channel.edit" or "position" not in c[2]]
    assert structural == []
    for key in ("rules", "verification", "roles", "tickets"):
        assert len(CFG.channel(guild, key).messages) == 1, "pas de message en double"


def test_announcement_channels_upgrade_once_community_is_enabled():
    guild = FakeGuild()
    run(guild)
    announcements = CFG.channel(guild, "announcements")
    assert not announcements.is_news()  # pas de Communauté : salon textuel
    guild.features.append("COMMUNITY")
    run(guild)
    assert announcements.is_news()
    assert CFG.channel(guild, "devlog").is_news()


def test_setup_refuses_without_administrator():
    guild = FakeGuild()

    class NoAdmin:
        administrator = False

    guild.me.guild_permissions = NoAdmin()
    try:
        run(guild)
    except Exception as exc:  # SetupError
        assert "Administrateur" in str(exc)
    else:
        raise AssertionError("SetupError attendu")
