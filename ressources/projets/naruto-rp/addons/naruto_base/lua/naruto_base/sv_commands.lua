--[[
    Naruto Base — commandes d'administration (console ou chat avec « ! »).

      nb_setrank   <joueur> <rang>      ex. nb_setrank Naruto chunin
      nb_givejutsu <joueur> <id>        ex. nb_givejutsu Naruto raiton_chidori
      nb_setxp     <joueur> <xp>
      nb_chakra    <joueur>             remplit le chakra
      nb_reset     <joueur>             le joueur recrée son personnage
      nb_list                           liste des jutsus, rangs, villages

    Permissions : via CAMI (ULX, SAM, DarkRP…) si présent, sinon « admin ».
]]

local PRIVILEGE = "NarutoBase_Admin"

if CAMI then
    CAMI.RegisterPrivilege({
        Name = PRIVILEGE,
        MinAccess = "admin",
        Description = "Commandes d'administration de Naruto Base",
    })
end

-- callback(true/false) ; la console du serveur a tous les droits
local function checkAccess(ply, callback)
    if not IsValid(ply) then return callback(true) end
    if CAMI then
        CAMI.PlayerHasAccess(ply, PRIVILEGE, function(allowed) callback(allowed == true) end)
    else
        callback(ply:IsAdmin())
    end
end

local function reply(ply, text)
    if IsValid(ply) then
        ply:ChatPrint("[Naruto Base] " .. text)
    else
        NB.Log(text)
    end
end

-- Cherche un joueur par SteamID64, SteamID ou morceau de pseudo
function NB.FindPlayer(query)
    if not query or query == "" then return nil end
    local lower = string.lower(query)
    local found
    for _, ply in ipairs(player.GetAll()) do
        if ply:SteamID64() == query or ply:SteamID() == query then return ply end
        if string.find(string.lower(ply:Nick()), lower, 1, true) then
            if found then return nil end -- plusieurs correspondances : ambigu
            found = ply
        end
    end
    return found
end

local COMMANDS = {}

COMMANDS.nb_setrank = function(caller, args)
    local target = NB.FindPlayer(args[1])
    if not target then return reply(caller, NB.L("player_not_found")) end
    if not NB.GetRank(args[2] or "") then return reply(caller, "Rang inconnu. Voir nb_list.") end
    NB.SetRank(target, args[2])
    reply(caller, NB.L("done"))
end

COMMANDS.nb_givejutsu = function(caller, args)
    local target = NB.FindPlayer(args[1])
    if not target then return reply(caller, NB.L("player_not_found")) end
    if not NB.GetJutsu(args[2] or "") then return reply(caller, "Jutsu inconnu. Voir nb_list.") end
    NB.LearnJutsu(target, args[2])
    reply(caller, NB.L("done"))
end

COMMANDS.nb_setxp = function(caller, args)
    local target = NB.FindPlayer(args[1])
    local xp = tonumber(args[2] or "")
    if not target or not xp then return reply(caller, "Usage : nb_setxp <joueur> <xp>") end
    local data = NB.GetData(target)
    if not data then return end
    data.xp = 0
    NB.AddXP(target, math.max(0, math.floor(xp)))
    NB.SyncPlayer(target)
    reply(caller, NB.L("done"))
end

COMMANDS.nb_chakra = function(caller, args)
    local target = NB.FindPlayer(args[1]) or (IsValid(caller) and caller or nil)
    if not target then return reply(caller, NB.L("player_not_found")) end
    NB.SetChakra(target, target:NB_GetMaxChakra())
    reply(caller, NB.L("done"))
end

COMMANDS.nb_reset = function(caller, args)
    local target = NB.FindPlayer(args[1])
    if not target then return reply(caller, NB.L("player_not_found")) end
    NB.ResetPlayer(target)
    reply(caller, NB.L("done"))
end

COMMANDS.nb_list = function(caller)
    local ranks, villages, jutsus = {}, {}, {}
    for _, r in ipairs(NB.Config.Ranks) do ranks[#ranks + 1] = r.id end
    for _, v in ipairs(NB.Config.Villages) do villages[#villages + 1] = v.id end
    for _, j in ipairs(NB.GetSortedJutsus()) do jutsus[#jutsus + 1] = j.id end
    reply(caller, "Rangs : " .. table.concat(ranks, ", "))
    reply(caller, "Villages : " .. table.concat(villages, ", "))
    reply(caller, "Jutsus : " .. table.concat(jutsus, ", "))
end

local function run(caller, name, args)
    checkAccess(caller, function(allowed)
        if not allowed then return reply(caller, NB.L("no_permission")) end
        COMMANDS[name](caller, args)
    end)
end

for name in pairs(COMMANDS) do
    concommand.Add(name, function(ply, _, args) run(ply, name, args) end)
end

-- Version chat : « !nb_setrank Naruto chunin »
hook.Add("PlayerSay", "NB_ChatCommands", function(ply, text)
    if text:sub(1, 1) ~= "!" then return end
    local parts = {}
    for word in text:sub(2):gmatch("%S+") do parts[#parts + 1] = word end
    local name = table.remove(parts, 1)
    if name and COMMANDS[name] then
        run(ply, name, parts)
        return ""
    end
end)
