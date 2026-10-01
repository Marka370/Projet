--[[
    Naruto Base — cœur partagé : recherches dans la config, données des joueurs.
]]

function NB.Log(...)
    print("[Naruto Base] " .. table.concat({ ... }, " "))
end

-- ───────────────────────────── Index de la configuration

local function indexById(list)
    local byId = {}
    for i, item in ipairs(list) do
        byId[item.id] = item
        item.index = i
    end
    return byId
end

function NB.BuildIndexes()
    local C = NB.Config
    NB.RanksById = indexById(C.Ranks)
    NB.VillagesById = indexById(C.Villages)
    NB.NaturesById = indexById(C.Natures)
    NB.ClansById = indexById(C.Clans)
end
NB.BuildIndexes()

function NB.GetRank(id) return NB.RanksById[id] end
function NB.GetVillage(id) return NB.VillagesById[id] end
function NB.GetNature(id) return NB.NaturesById[id] end
function NB.GetClan(id) return NB.ClansById[id] end

-- rankId est-il au moins égal à minRankId ?
function NB.RankAtLeast(rankId, minRankId)
    local rank, minRank = NB.GetRank(rankId), NB.GetRank(minRankId)
    if not rank or not minRank then return false end
    return rank.index >= minRank.index
end

function NB.ComputeMaxChakra(rankId, clanId)
    local rank = NB.GetRank(rankId) or NB.Config.Ranks[1]
    local clan = NB.GetClan(clanId)
    local mult = clan and clan.chakraMult or 1
    return math.floor(rank.maxChakra * mult)
end

-- Rang automatique le plus haut atteignable avec cette XP
function NB.RankForXP(xp)
    local best
    for _, rank in ipairs(NB.Config.Ranks) do
        if rank.xp ~= nil and xp >= rank.xp then
            best = rank
        end
    end
    return best
end

-- ───────────────────────────── Accès aux infos d'un joueur
-- Les valeurs sont synchronisées automatiquement à tous les clients (NW2).

local PLAYER = FindMetaTable("Player")

function PLAYER:NB_GetChakra() return self:GetNW2Float("nb_chakra", 0) end
function PLAYER:NB_GetMaxChakra() return self:GetNW2Int("nb_max_chakra", 100) end
function PLAYER:NB_GetRank() return self:GetNW2String("nb_rank", NB.Config.StartRank) end
function PLAYER:NB_GetVillage() return self:GetNW2String("nb_village", "") end
function PLAYER:NB_GetClan() return self:GetNW2String("nb_clan", "aucun") end
function PLAYER:NB_GetNature() return self:GetNW2String("nb_nature", "") end
function PLAYER:NB_IsCreated() return self:GetNW2Bool("nb_created", false) end

function PLAYER:NB_GetRankName()
    local rank = NB.GetRank(self:NB_GetRank())
    return rank and rank.name or "?"
end
