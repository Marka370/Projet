--[[
    Naruto Base — HUD : identité du ninja, vie, chakra, progression.
]]

local T = NB.Config.Theme
local S = NB.UI.Scale

local HIDDEN = { CHudHealth = true, CHudBattery = true }
hook.Add("HUDShouldDraw", "NB_HideDefault", function(name)
    if NB.Config.HideDefaultHUD and HIDDEN[name] then return false end
end)

-- Valeurs lissées pour des barres qui glissent au lieu de sauter
local smoothHealth, smoothChakra = 0, 0

local function nextRankInfo(xp, rankId)
    local current = NB.GetRank(rankId)
    for _, rank in ipairs(NB.Config.Ranks) do
        if rank.xp ~= nil and current and rank.index > current.index then
            return rank, current.xp or 0
        end
    end
    return nil
end

hook.Add("HUDPaint", "NB_HUD", function()
    local ply = LocalPlayer()
    if not IsValid(ply) or not ply:Alive() then return end

    local w, h = S(360), S(122)
    local x, y = S(20), ScrH() - h - S(20)

    if not ply:NB_IsCreated() then
        draw.SimpleText("Crée ton personnage pour commencer (commande : nb_creation)", "NB.Small",
            x, y + h, T.textDim, TEXT_ALIGN_LEFT, TEXT_ALIGN_BOTTOM)
        return
    end

    local village = NB.GetVillage(ply:NB_GetVillage())
    local villageColor = village and village.color or T.accent
    local nature = NB.GetNature(ply:NB_GetNature())
    local clan = NB.GetClan(ply:NB_GetClan())

    -- Fond
    draw.RoundedBox(8, x, y, w, h, T.background)
    draw.RoundedBoxEx(8, x, y, S(6), h, villageColor, true, false, true, false)

    -- Identité
    local px = x + S(18)
    draw.SimpleText(ply:Nick(), "NB.Medium", px, y + S(18), T.text, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    local subtitle = (village and village.name or "?") .. "  ·  " .. ply:NB_GetRankName()
    if clan and clan.id ~= "aucun" then subtitle = subtitle .. "  ·  " .. clan.name end
    draw.SimpleText(subtitle, "NB.Tiny", px, y + S(40), villageColor, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    if nature then
        draw.SimpleText(nature.name, "NB.Tiny", x + w - S(12), y + S(18), nature.color, TEXT_ALIGN_RIGHT, TEXT_ALIGN_CENTER)
    end

    -- Barres
    local barW, barH = w - S(30), S(18)
    local dt = FrameTime() * 8
    smoothHealth = Lerp(dt, smoothHealth, ply:Health())
    smoothChakra = Lerp(dt, smoothChakra, ply:NB_GetChakra())

    local maxHealth, maxChakra = math.max(ply:GetMaxHealth(), 1), math.max(ply:NB_GetMaxChakra(), 1)
    NB.UI.DrawBar(px, y + S(56), barW, barH, smoothHealth / maxHealth, T.health,
        "Vie  " .. math.max(ply:Health(), 0) .. " / " .. maxHealth)
    NB.UI.DrawBar(px, y + S(80), barW, barH, smoothChakra / maxChakra, T.chakra,
        "Chakra  " .. math.floor(ply:NB_GetChakra()) .. " / " .. maxChakra)

    -- Progression vers le rang suivant
    local nextRank, fromXP = nextRankInfo(NB.Local.xp, ply:NB_GetRank())
    if nextRank then
        local fraction = (NB.Local.xp - fromXP) / math.max(nextRank.xp - fromXP, 1)
        NB.UI.DrawBar(px, y + S(104), barW, S(6), fraction, T.xp)
    end
end)
