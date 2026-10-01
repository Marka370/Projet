"""Tests de l'addon Garry's Mod naruto_base, exécuté dans un vrai Lua 5.1
(via lupa) avec une simulation de l'API GMod (tests/gmod_stubs.lua)."""

import json
from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa.lua51")

ROOT = Path(__file__).resolve().parent.parent
ADDON = ROOT / "ressources" / "projets" / "naruto-rp" / "addons" / "naruto_base"
STUBS = Path(__file__).with_name("gmod_stubs.lua")


def lua_to_py(value):
    if lupa.lua_type(value) != "table":
        return value
    items = dict(value.items())
    keys = list(items)
    if keys and all(isinstance(k, int) for k in keys) and sorted(keys) == list(range(1, len(keys) + 1)):
        return [lua_to_py(items[i]) for i in range(1, len(keys) + 1)]
    return {str(k): lua_to_py(v) for k, v in items.items()}


@pytest.fixture
def gmod():
    lua = lupa.LuaRuntime(unpack_returned_tuples=True)
    g = lua.globals()
    g.ADDON_ROOT = str(ADDON)
    g.PY_TO_JSON = lambda t: json.dumps(lua_to_py(t))
    g.PY_FROM_JSON = lambda s: lua.table_from(json.loads(s), recursive=True)

    def list_lua(pattern):
        folder = ADDON / "lua" / Path(pattern).parent
        return lua.table_from(sorted(p.name for p in folder.glob(Path(pattern).name)))

    g.PY_LIST_LUA = list_lua
    lua.execute(STUBS.read_text(encoding="utf-8"))
    lua.execute('include("autorun/sh_naruto_base.lua")')
    return lua


def notices(lua, ply):
    """Textes des notifications envoyées à un joueur."""
    return list(lua.eval("NoticesFor")(ply).values())


def connect(lua, nick="Naruto"):
    ply = lua.eval(f'NewPlayer("{nick}")')
    lua.eval("hook.Run")("PlayerInitialSpawn", ply)
    lua.eval("net.FromClient")(ply, "nb_ready")
    return ply


def create(lua, ply, village="konoha", clan="uchiha", nature="katon"):
    lua.eval("net.FromClient")(ply, "nb_create", village, clan, nature)


def advance(lua, seconds):
    lua.eval("timer.Advance")(seconds)


# ------------------------------------------------------------------ chargement


def test_addon_loads_all_jutsus(gmod):
    ids = set(gmod.eval("NB.JutsuList").values())
    assert ids == {
        "katon_goukakyu", "neutre_iryo", "neutre_kawarimi",
        "neutre_rasengan", "neutre_shunshin", "raiton_chidori",
    }
    assert any("chargée" in line for line in gmod.eval("LOGS").values())


@pytest.mark.parametrize("path", sorted(str(p.relative_to(ADDON)) for p in ADDON.rglob("*.lua")))
def test_every_lua_file_compiles(gmod, path):
    """Vérifie la syntaxe de tous les fichiers, y compris client, arme et entité."""
    source = (ADDON / path).read_text(encoding="utf-8")
    ok, err = gmod.eval("Compiles")(source, path)
    assert ok, err


# ------------------------------------------------------------------ création


def test_new_player_must_create_character(gmod):
    ply = connect(gmod)
    sync = gmod.eval("net.Last")("nb_sync", ply)
    assert json.loads(sync["values"][1])["created"] is False
    assert ply.NB_IsCreated(ply) is False


def test_create_rejects_clan_from_other_village(gmod):
    ply = connect(gmod)
    create(gmod, ply, village="suna", clan="uchiha")
    assert ply.NB_IsCreated(ply) is False
    assert "Choix invalide." in notices(gmod, ply)


def test_create_rejects_unknown_values(gmod):
    ply = connect(gmod)
    create(gmod, ply, village="konoha", clan="aucun", nature="glace")
    assert ply.NB_IsCreated(ply) is False


def test_create_character(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    assert ply.NB_IsCreated(ply) is True
    assert ply.NB_GetVillage(ply) == "konoha"
    assert ply.NB_GetMaxChakra(ply) == 66  # 60 (Académie) x 1.1 (Uchiha)
    assert ply.NB_GetChakra(ply) == 66
    assert ply.SteamID64(ply) in dict(gmod.eval("DB").items())

    create(gmod, ply, village="suna", clan="aucun", nature="futon")
    assert ply.NB_GetVillage(ply) == "konoha", "on ne recrée pas un personnage existant"


# ------------------------------------------------------------------ jutsus


def test_known_jutsus_depend_on_rank_and_nature(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    knows = gmod.eval("NB.KnowsJutsu")
    assert knows(ply, "neutre_shunshin")
    assert not knows(ply, "katon_goukakyu"), "rang Genin requis"
    assert not knows(ply, "raiton_chidori"), "mauvaise nature"


def test_cast_costs_chakra_and_starts_cooldown(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    advance(gmod, 1)
    gmod.eval("net.FromClient")(ply, "nb_cast", "neutre_shunshin")

    assert ply.NB_GetChakra(ply) == 56
    assert ply.velocity is not None
    cooldown = gmod.eval("net.Last")("nb_cooldown", ply)
    assert cooldown["values"][1] == "neutre_shunshin"
    assert gmod.eval("net.Last")("nb_gesture") is not None
    assert gmod.eval("NB.GetData")(ply).xp == 2

    advance(gmod, 1)  # pendant la recharge (3 s)
    gmod.eval("net.FromClient")(ply, "nb_cast", "neutre_shunshin")
    assert ply.NB_GetChakra(ply) == 56
    assert any("recharge" in n for n in notices(gmod, ply))


def test_cast_rate_limit(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    advance(gmod, 1)
    gmod.eval("net.FromClient")(ply, "nb_cast", "neutre_kawarimi_inconnu")
    count = len(notices(gmod, ply))
    gmod.eval("net.FromClient")(ply, "nb_cast", "neutre_kawarimi_inconnu")  # même instant
    assert len(notices(gmod, ply)) == count


def test_cast_without_enough_chakra(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    gmod.eval("NB.SetChakra")(ply, 5)
    advance(gmod, 1)
    gmod.eval("net.FromClient")(ply, "nb_cast", "neutre_shunshin")
    assert ply.NB_GetChakra(ply) == 5
    assert "Pas assez de chakra !" in notices(gmod, ply)


def test_refused_or_crashing_jutsu_costs_nothing(gmod):
    gmod.execute("""
        NB.RegisterJutsu({ id = "test_refuse", name = "Refus", chakra = 10, cooldown = 5,
            OnCast = function() return false end })
        NB.RegisterJutsu({ id = "test_crash", name = "Crash", chakra = 10, cooldown = 5,
            OnCast = function() error("boum") end })
    """)
    ply = connect(gmod)
    create(gmod, ply)
    try_cast = gmod.eval("NB.TryCast")
    assert try_cast(ply, "test_refuse") is False
    assert try_cast(ply, "test_crash") is False
    assert ply.NB_GetChakra(ply) == 66
    assert gmod.eval("NB.GetCooldownLeft")(ply, "test_refuse") == 0
    assert "La technique a échoué." in notices(gmod, ply)


def test_heal_jutsu_refuses_when_full_health(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    gmod.eval("NB.SetRank")(ply, "genin")
    advance(gmod, 1)
    try_cast = gmod.eval("NB.TryCast")
    assert try_cast(ply, "neutre_iryo") is False
    ply.health = 40
    assert try_cast(ply, "neutre_iryo") is True
    assert ply.health == 75


def test_long_jutsu_id_is_ignored(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    advance(gmod, 1)
    before = len(gmod.eval("net.sent"))
    gmod.eval("net.FromClient")(ply, "nb_cast", "x" * 500)
    assert len(gmod.eval("net.sent")) == before


# ------------------------------------------------------------------ progression


def test_xp_promotes_rank_and_unlocks_jutsus(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    gmod.eval("NB.AddXP")(ply, 100)
    assert ply.NB_GetRank(ply) == "genin"
    assert ply.NB_GetMaxChakra(ply) == 110
    assert "Promotion ! Tu es maintenant Genin." in notices(gmod, ply)
    assert gmod.eval("NB.KnowsJutsu")(ply, "katon_goukakyu")


def test_xp_never_demotes_named_rank(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    gmod.eval("NB.SetRank")(ply, "anbu")
    gmod.eval("NB.AddXP")(ply, 5000)
    assert ply.NB_GetRank(ply) == "anbu"


def test_chakra_regen_and_meditation(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    gmod.eval("NB.SetChakra")(ply, 0)
    gmod.eval("timer.RunTimer")("NB_ChakraRegen")
    assert ply.NB_GetChakra(ply) == 1  # 2/s pendant 0,5 s
    ply.crouching = True
    gmod.eval("timer.RunTimer")("NB_ChakraRegen")
    assert ply.NB_GetChakra(ply) == 4  # x3 en méditation


# ------------------------------------------------------------------ barre de jutsus


def test_set_slot_validates_input(gmod):
    ply = connect(gmod)
    create(gmod, ply)
    from_client = gmod.eval("net.FromClient")
    slots = lambda: dict(gmod.eval("NB.GetData")(ply).slots.items())  # noqa: E731

    from_client(ply, "nb_setslot", 1, "neutre_shunshin")
    assert slots() == {1: "neutre_shunshin"}

    advance(gmod, 1)
    from_client(ply, "nb_setslot", 2, "raiton_chidori")  # pas connu
    advance(gmod, 1)
    from_client(ply, "nb_setslot", 9, "neutre_kawarimi")  # emplacement invalide
    assert slots() == {1: "neutre_shunshin"}

    advance(gmod, 1)
    from_client(ply, "nb_setslot", 3, "neutre_shunshin")  # déplacé, pas dupliqué
    assert slots() == {3: "neutre_shunshin"}


# ------------------------------------------------------------------ sauvegarde


def test_data_survives_reconnection(gmod):
    ply = connect(gmod)
    create(gmod, ply, village="kumo", clan="yotsuki", nature="raiton")
    gmod.eval("NB.AddXP")(ply, 450)
    gmod.eval("net.FromClient")(ply, "nb_setslot", 2, "raiton_chidori")
    gmod.eval("NB.LearnJutsu")(ply, "katon_goukakyu")
    steamid = ply.SteamID64(ply)

    gmod.eval("hook.Run")("PlayerDisconnected", ply)
    gmod.eval("RemovePlayer")(ply)

    again = gmod.eval('NewPlayer("Retour")')
    again.steamid64 = steamid
    gmod.eval("hook.Run")("PlayerInitialSpawn", again)
    assert again.NB_GetVillage(again) == "kumo"
    assert again.NB_GetRank(again) == "chunin"
    data = gmod.eval("NB.GetData")(again)
    assert data.slots[2] == "raiton_chidori"
    assert data.learned["katon_goukakyu"] is True


def test_corrupted_save_is_sanitized(gmod):
    data = gmod.eval("NB.DB.Deserialize")(gmod.eval("""{
        created = true, village = "atlantide", rank = "dieu", xp = -50,
        learned = { 42, "katon_goukakyu" }, slots = { "", 7 }
    }"""))
    assert data.created is False  # village invalide => personnage à recréer
    assert data.rank == "academie"
    assert data.xp == 0
    assert dict(data.learned.items()) == {"katon_goukakyu": True}
    assert dict(data.slots.items()) == {}


# ------------------------------------------------------------------ commandes admin


def test_admin_commands_require_permission(gmod):
    target = connect(gmod, "Sasuke")
    create(gmod, target)
    user = connect(gmod, "Visiteur")
    command = gmod.eval("concommand.list")["nb_setrank"]

    command(user, "nb_setrank", gmod.table_from(["Sasuke", "jonin"]))
    assert target.NB_GetRank(target) == "academie"
    assert user.chat[1] == "[Naruto Base] Tu n'as pas la permission."

    user.admin = True
    command(user, "nb_setrank", gmod.table_from(["Sasuke", "jonin"]))
    assert target.NB_GetRank(target) == "jonin"

    command(None, "nb_setrank", gmod.table_from(["Sasuke", "kage"]))  # console du serveur
    assert target.NB_GetRank(target) == "kage"


def test_chat_command(gmod):
    target = connect(gmod, "Sakura")
    create(gmod, target)
    admin = connect(gmod, "Tsunade")
    admin.admin = True
    result = gmod.eval("RunHook")("PlayerSay", admin, "!nb_givejutsu Sakura raiton_chidori")
    assert result == ""
    assert gmod.eval("NB.KnowsJutsu")(target, "raiton_chidori")
