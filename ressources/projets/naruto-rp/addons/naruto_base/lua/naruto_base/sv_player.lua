--[[
    Naruto Base — gestion des joueurs côté serveur :
    chargement, création de personnage, chakra, XP, rangs, synchronisation.
]]

util.AddNetworkString("nb_ready")      -- client → serveur : prêt à recevoir ses données
util.AddNetworkString("nb_sync")       -- serveur → client : données du joueur
util.AddNetworkString("nb_create")     -- client → serveur : création du personnage
util.AddNetworkString("nb_setslot")    -- client → serveur : assigner un jutsu à un emplacement
util.AddNetworkString("nb_cast")       -- client → serveur : lancer un jutsu
util.AddNetworkString("nb_cooldown")   -- serveur → client : début d'un cooldown
util.AddNetworkString("nb_gesture")    -- serveur → clients : animation d'un joueur
util.AddNetworkString("nb_notify")     -- serveur → client : message à l'écran

-- Données en mémoire, indexées par joueur
NB.Data = NB.Data or setmetatable({}, { __mode = "k" })

function NB.GetData(ply)
    return NB.Data[ply]
end

function NB.GetLearnedSet(ply)
    local data = NB.Data[ply]
    return data and data.learned or {}
end

-- ───────────────────────────── Anti-spam des messages réseau

local lastMessage = setmetatable({}, { __mode = "k" })

-- true si le joueur envoie ce message trop souvent
function NB.IsRateLimited(ply, key, delay)
    lastMessage[ply] = lastMessage[ply] or {}
    local now = CurTime()
    local last = lastMessage[ply][key]
    if last and now - last < delay then return true end
    lastMessage[ply][key] = now
    return false
end

-- ───────────────────────────── Notifications

function NB.Notify(ply, text, kind)
    net.Start("nb_notify")
    net.WriteString(text)
    net.WriteString(kind or "info")
    net.Send(ply)
end

-- ───────────────────────────── Application des données

function NB.SetChakra(ply, amount)
    amount = math.Clamp(amount, 0, ply:NB_GetMaxChakra())
    ply:SetNW2Float("nb_chakra", amount)
end

function NB.ApplyData(ply)
    local data = NB.Data[ply]
    if not data then return end
    ply:SetNW2Bool("nb_created", data.created)
    ply:SetNW2String("nb_rank", data.rank)
    ply:SetNW2String("nb_village", data.village)
    ply:SetNW2String("nb_clan", data.clan)
    ply:SetNW2String("nb_nature", data.nature)
    ply:SetNW2Int("nb_max_chakra", NB.ComputeMaxChakra(data.rank, data.clan))
    NB.SetChakra(ply, ply:NB_GetChakra())
end

function NB.SyncPlayer(ply)
    local data = NB.Data[ply]
    if not data then return end
    local payload = NB.DB.Serialize(data)
    net.Start("nb_sync")
    net.WriteString(util.TableToJSON(payload))
    net.Send(ply)
end

function NB.SavePlayer(ply)
    local data = NB.Data[ply]
    if not data or not data.dirty then return end
    if NB.DB.Save(ply:SteamID64(), data) then
        data.dirty = false
    end
end

function NB.MarkDirty(ply)
    local data = NB.Data[ply]
    if data then data.dirty = true end
end

function NB.SaveAll()
    for _, ply in ipairs(player.GetAll()) do
        NB.SavePlayer(ply)
    end
end

-- ───────────────────────────── Progression

function NB.SetRank(ply, rankId)
    local data = NB.Data[ply]
    local rank = NB.GetRank(rankId)
    if not data or not rank then return false end
    data.rank = rankId
    NB.MarkDirty(ply)
    NB.ApplyData(ply)
    NB.SyncPlayer(ply)
    NB.Notify(ply, NB.L("rank_up", rank.name), "success")
    hook.Run("NB_RankChanged", ply, rankId)
    return true
end

function NB.AddXP(ply, amount)
    local data = NB.Data[ply]
    if not data then return end
    data.xp = data.xp + amount
    NB.MarkDirty(ply)

    if NB.Config.AutoRankUp then
        local target = NB.RankForXP(data.xp)
        local current = NB.GetRank(data.rank)
        -- On ne rétrograde jamais, et on ne dépasse pas les rangs « nommés »
        if target and current and target.index > current.index then
            NB.SetRank(ply, target.id)
            return
        end
    end
    NB.SyncPlayer(ply)
end

function NB.LearnJutsu(ply, id)
    local data = NB.Data[ply]
    local jutsu = NB.GetJutsu(id)
    if not data or not jutsu then return false end
    data.learned[id] = true
    NB.MarkDirty(ply)
    NB.SyncPlayer(ply)
    NB.Notify(ply, NB.L("jutsu_learned", jutsu.name), "success")
    return true
end

-- Remet le personnage à zéro (le joueur repasse par la création)
function NB.ResetPlayer(ply)
    NB.Data[ply] = NB.DefaultData()
    NB.Data[ply].dirty = true
    NB.Cooldowns[ply] = nil
    NB.ApplyData(ply)
    NB.SavePlayer(ply)
    NB.SyncPlayer(ply)
end

-- ───────────────────────────── Cycle de vie

hook.Add("PlayerInitialSpawn", "NB_Load", function(ply)
    local data = NB.DB.Load(ply:SteamID64()) or NB.DefaultData()
    NB.Data[ply] = data
    NB.ApplyData(ply)
    NB.SetChakra(ply, ply:NB_GetMaxChakra())
end)

hook.Add("PlayerSpawn", "NB_Spawn", function(ply)
    if NB.Data[ply] then
        NB.SetChakra(ply, ply:NB_GetMaxChakra())
    end
end)

hook.Add("PlayerDisconnected", "NB_Save", function(ply)
    NB.SavePlayer(ply)
    NB.Data[ply] = nil
    NB.Cooldowns[ply] = nil
end)

hook.Add("ShutDown", "NB_SaveAll", NB.SaveAll)
timer.Create("NB_AutoSave", NB.Config.SaveInterval, 0, NB.SaveAll)

-- Régénération du chakra (méditation : accroupi et immobile)
timer.Create("NB_ChakraRegen", NB.Config.ChakraRegenInterval, 0, function()
    local interval = NB.Config.ChakraRegenInterval
    for _, ply in ipairs(player.GetAll()) do
        local data = NB.Data[ply]
        if data and data.created and ply:Alive() then
            local rank = NB.GetRank(data.rank)
            local amount = rank.regen * interval
            if ply:Crouching() and ply:GetVelocity():Length() < 5 then
                amount = amount * NB.Config.MeditationMultiplier
            end
            local chakra = ply:NB_GetChakra()
            if chakra < ply:NB_GetMaxChakra() then
                NB.SetChakra(ply, chakra + amount)
            end
        end
    end
end)

-- ───────────────────────────── Messages des clients
-- Règle d'or : ne JAMAIS faire confiance à ce qu'envoie le client.

net.Receive("nb_ready", function(_, ply)
    if ply.NB_Ready then return end
    ply.NB_Ready = true
    NB.SyncPlayer(ply)
end)

net.Receive("nb_create", function(_, ply)
    if NB.IsRateLimited(ply, "create", 1) then return end
    local data = NB.Data[ply]
    if not data then return end
    if data.created then
        NB.Notify(ply, NB.L("already_created"), "error")
        return
    end

    local villageId = net.ReadString()
    local clanId = net.ReadString()
    local natureId = net.ReadString()

    local village = NB.GetVillage(villageId)
    local clan = NB.GetClan(clanId)
    local nature = NB.GetNature(natureId)
    local clanAllowed = clan and (clan.village == nil or clan.village == villageId)
    if not village or not nature or not clanAllowed then
        NB.Notify(ply, NB.L("invalid_choice"), "error")
        return
    end

    data.village = villageId
    data.clan = clanId
    data.nature = natureId
    data.created = true
    data.dirty = true

    NB.ApplyData(ply)
    NB.SetChakra(ply, ply:NB_GetMaxChakra())
    NB.SavePlayer(ply)
    NB.SyncPlayer(ply)
    NB.Notify(ply, NB.L("created", village.name), "success")
    hook.Run("NB_CharacterCreated", ply)
end)

net.Receive("nb_setslot", function(_, ply)
    if NB.IsRateLimited(ply, "setslot", 0.1) then return end
    local data = NB.Data[ply]
    if not data then return end

    local slot = net.ReadUInt(4)
    local id = net.ReadString()
    if slot < 1 or slot > #NB.Config.HotbarKeys then return end

    if id == "" then
        data.slots[slot] = nil
    elseif NB.KnowsJutsu(ply, id) then
        -- Un jutsu n'occupe qu'un seul emplacement
        for i = 1, #NB.Config.HotbarKeys do
            if data.slots[i] == id then data.slots[i] = nil end
        end
        data.slots[slot] = id
    else
        return
    end

    data.dirty = true
    NB.SyncPlayer(ply)
end)
