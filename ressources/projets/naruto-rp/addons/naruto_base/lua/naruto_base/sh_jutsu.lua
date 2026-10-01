--[[
    Naruto Base — registre des jutsus et règles d'utilisation (partagé).

    Créer un jutsu : voir naruto_base/jutsus/ et le README.
]]

NB.Jutsus = NB.Jutsus or {}
NB.JutsuList = NB.JutsuList or {}

-- Cooldowns : [joueur][id du jutsu] = fin du cooldown (CurTime)
NB.Cooldowns = NB.Cooldowns or setmetatable({}, { __mode = "k" })

function NB.RegisterJutsu(def)
    assert(istable(def), "RegisterJutsu : une table est attendue")
    assert(isstring(def.id) and def.id ~= "", "RegisterJutsu : « id » manquant")
    assert(isstring(def.name), "RegisterJutsu (" .. def.id .. ") : « name » manquant")
    assert(isnumber(def.chakra) and def.chakra >= 0, "RegisterJutsu (" .. def.id .. ") : « chakra » invalide")
    assert(isnumber(def.cooldown) and def.cooldown >= 0, "RegisterJutsu (" .. def.id .. ") : « cooldown » invalide")
    assert(isfunction(def.OnCast), "RegisterJutsu (" .. def.id .. ") : fonction « OnCast » manquante")

    def.nature = def.nature or "neutre"
    def.rank = def.rank or NB.Config.StartRank
    def.description = def.description or ""
    if def.auto == nil then def.auto = true end

    assert(def.nature == "neutre" or NB.GetNature(def.nature),
        "RegisterJutsu (" .. def.id .. ") : nature inconnue « " .. tostring(def.nature) .. " »")
    assert(NB.GetRank(def.rank), "RegisterJutsu (" .. def.id .. ") : rang inconnu « " .. tostring(def.rank) .. " »")
    assert(def.clan == nil or NB.GetClan(def.clan), "RegisterJutsu (" .. def.id .. ") : clan inconnu")

    if not NB.Jutsus[def.id] then
        table.insert(NB.JutsuList, def.id)
    end
    NB.Jutsus[def.id] = def
    return def
end

function NB.GetJutsu(id)
    return NB.Jutsus[id]
end

-- Liste triée par rang puis par nom (pour les menus)
function NB.GetSortedJutsus()
    local list = {}
    for _, id in ipairs(NB.JutsuList) do
        list[#list + 1] = NB.Jutsus[id]
    end
    table.sort(list, function(a, b)
        local ra, rb = NB.GetRank(a.rank).index, NB.GetRank(b.rank).index
        if ra ~= rb then return ra < rb end
        return a.name < b.name
    end)
    return list
end

-- ───────────────────────────── Apprentissage

-- Le joueur remplit-il les conditions (rang, nature, clan, village) ?
function NB.MeetsRequirements(ply, jutsu)
    if not NB.RankAtLeast(ply:NB_GetRank(), jutsu.rank) then return false, "rank" end
    if jutsu.nature ~= "neutre" and jutsu.nature ~= ply:NB_GetNature() then return false, "nature" end
    if jutsu.clan and jutsu.clan ~= ply:NB_GetClan() then return false, "clan" end
    if jutsu.village and jutsu.village ~= ply:NB_GetVillage() then return false, "village" end
    return true
end

-- Jutsus appris explicitement (donnés par un admin, un PNJ, un rouleau…)
-- Implémentée côté serveur (sv_player.lua) et côté client (cl_net.lua).
function NB.GetLearnedSet(ply)
    return {}
end

function NB.KnowsJutsu(ply, id)
    local jutsu = NB.GetJutsu(id)
    if not jutsu then return false end
    if NB.GetLearnedSet(ply)[id] then return true end
    -- Jutsus « auto » : connus dès que les conditions sont remplies
    return jutsu.auto and (NB.MeetsRequirements(ply, jutsu)) or false
end

-- ───────────────────────────── Cooldowns

function NB.GetCooldownEnd(ply, id)
    local cds = NB.Cooldowns[ply]
    return cds and cds[id] or 0
end

function NB.SetCooldownEnd(ply, id, endTime)
    NB.Cooldowns[ply] = NB.Cooldowns[ply] or {}
    NB.Cooldowns[ply][id] = endTime
end

function NB.GetCooldownLeft(ply, id)
    return math.max(0, NB.GetCooldownEnd(ply, id) - CurTime())
end

-- ───────────────────────────── Peut-on lancer ce jutsu ?
-- Retourne true, ou false + un message déjà traduit.
function NB.CanCast(ply, id)
    local jutsu = NB.GetJutsu(id)
    if not jutsu then return false, NB.L("unknown_jutsu") end
    if not ply:NB_IsCreated() then return false, NB.L("not_created") end
    if not ply:Alive() then return false, NB.L("dead") end
    if not NB.KnowsJutsu(ply, id) then return false, NB.L("not_learned") end

    local left = NB.GetCooldownLeft(ply, id)
    if left > 0 then return false, NB.L("cooldown", string.format("%.1f", left)) end
    if ply:NB_GetChakra() < jutsu.chakra then return false, NB.L("no_chakra") end

    if jutsu.CanCast then
        local ok, reason = jutsu.CanCast(ply, jutsu)
        if ok == false then return false, reason or NB.L("cast_failed") end
    end
    return true
end

-- ───────────────────────────── Outils pour écrire des jutsus (serveur)

NB.Util = NB.Util or {}

-- Trace devant le joueur ; renvoie le résultat de util.TraceHull
function NB.Util.TraceFront(ply, distance, size)
    size = size or 12
    local start = ply:EyePos()
    return util.TraceHull({
        start = start,
        endpos = start + ply:GetAimVector() * distance,
        mins = Vector(-size, -size, -size),
        maxs = Vector(size, size, size),
        filter = ply,
        mask = MASK_SHOT_HULL,
    })
end

-- Cible vivante (joueur ou PNJ) devant le joueur, ou nil
function NB.Util.TargetInFront(ply, distance)
    local tr = NB.Util.TraceFront(ply, distance, 16)
    local ent = tr.Entity
    if IsValid(ent) and (ent:IsPlayer() or ent:IsNPC() or ent:IsNextBot()) then
        return ent, tr
    end
    return nil, tr
end

function NB.Util.Effect(name, pos, scale, normal)
    local data = EffectData()
    data:SetOrigin(pos)
    data:SetScale(scale or 1)
    data:SetMagnitude(scale or 1)
    data:SetNormal(normal or Vector(0, 0, 1))
    util.Effect(name, data, true, true)
end

-- Inflige des dégâts « propres » (attribués au lanceur)
function NB.Util.Damage(attacker, target, amount, dmgType, force)
    local info = DamageInfo()
    info:SetDamage(amount)
    info:SetAttacker(attacker)
    info:SetInflictor(attacker)
    info:SetDamageType(dmgType or DMG_GENERIC)
    if force then info:SetDamageForce(force) end
    target:TakeDamageInfo(info)
end
