--[[
    Naruto Base — sauvegarde des joueurs (SQLite intégré à GMod, fichier sv.db).
    Aucune installation nécessaire.
]]

NB.DB = NB.DB or {}

local TABLE = "nb_players"

sql.Query("CREATE TABLE IF NOT EXISTS " .. TABLE .. " (steamid TEXT PRIMARY KEY, data TEXT NOT NULL)")

function NB.DefaultData()
    return {
        created = false,
        village = "",
        clan = "aucun",
        nature = "",
        rank = NB.Config.StartRank,
        xp = 0,
        learned = {},   -- [id du jutsu] = true
        slots = {},     -- [numéro d'emplacement] = id du jutsu
    }
end

-- Données en mémoire → table enregistrable en JSON (sans « trous »)
function NB.DB.Serialize(data)
    local learned = {}
    for id in pairs(data.learned) do
        learned[#learned + 1] = id
    end
    table.sort(learned)

    local slots = {}
    for i = 1, #NB.Config.HotbarKeys do
        slots[i] = data.slots[i] or ""
    end

    return {
        created = data.created,
        village = data.village,
        clan = data.clan,
        nature = data.nature,
        rank = data.rank,
        xp = data.xp,
        learned = learned,
        slots = slots,
    }
end

-- JSON lu → données en mémoire, en ignorant tout ce qui est invalide
function NB.DB.Deserialize(saved)
    local data = NB.DefaultData()
    if not istable(saved) then return data end

    data.created = saved.created == true
    if isstring(saved.village) and NB.GetVillage(saved.village) then data.village = saved.village end
    if isstring(saved.clan) and NB.GetClan(saved.clan) then data.clan = saved.clan end
    if isstring(saved.nature) and NB.GetNature(saved.nature) then data.nature = saved.nature end
    if isstring(saved.rank) and NB.GetRank(saved.rank) then data.rank = saved.rank end
    if isnumber(saved.xp) then data.xp = math.max(0, math.floor(saved.xp)) end

    if istable(saved.learned) then
        for _, id in ipairs(saved.learned) do
            if isstring(id) then data.learned[id] = true end
        end
    end
    if istable(saved.slots) then
        for i = 1, #NB.Config.HotbarKeys do
            local id = saved.slots[i]
            if isstring(id) and id ~= "" then data.slots[i] = id end
        end
    end

    -- Un personnage sans village/nature valides doit être recréé
    if data.village == "" or data.nature == "" then data.created = false end
    return data
end

function NB.DB.Load(steamID)
    local raw = sql.QueryValue("SELECT data FROM " .. TABLE .. " WHERE steamid = " .. sql.SQLStr(steamID))
    if not raw then return nil end
    return NB.DB.Deserialize(util.JSONToTable(raw))
end

function NB.DB.Save(steamID, data)
    local json = util.TableToJSON(NB.DB.Serialize(data))
    local result = sql.Query("REPLACE INTO " .. TABLE .. " (steamid, data) VALUES ("
        .. sql.SQLStr(steamID) .. ", " .. sql.SQLStr(json) .. ")")
    if result == false then
        NB.Log("Erreur SQL : " .. tostring(sql.LastError()))
        return false
    end
    return true
end

function NB.DB.Delete(steamID)
    sql.Query("DELETE FROM " .. TABLE .. " WHERE steamid = " .. sql.SQLStr(steamID))
end
