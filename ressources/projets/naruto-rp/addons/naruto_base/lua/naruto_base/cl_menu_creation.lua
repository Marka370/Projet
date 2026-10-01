--[[
    Naruto Base — menu de création du personnage : village, clan, nature de chakra.
    S'ouvre automatiquement à la première connexion (commande : nb_creation).
]]

local T = NB.Config.Theme
local S = NB.UI.Scale

local frame

local function column(parent, title)
    local panel = vgui.Create("DPanel", parent)
    panel:Dock(LEFT)
    panel:DockMargin(0, 0, S(10), 0)
    panel:DockPadding(S(10), S(40), S(10), S(10))
    panel.Paint = function(_, w, h)
        draw.RoundedBox(6, 0, 0, w, h, Color(0, 0, 0, 90))
        draw.SimpleText(title, "NB.Medium", S(12), S(20), T.accent, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    end
    local scroll = vgui.Create("DScrollPanel", panel)
    scroll:Dock(FILL)
    return panel, scroll
end

function NB.OpenCreationMenu()
    if IsValid(frame) then frame:Remove() end
    if NB.Local.created then return end

    local choice = { village = nil, clan = "aucun", nature = nil }

    frame = NB.UI.Frame("Création de ton ninja", 1100, 640, false)

    local columns = vgui.Create("DPanel", frame)
    columns:Dock(FILL)
    columns.Paint = nil

    local footer = vgui.Create("DPanel", frame)
    footer:Dock(BOTTOM)
    footer:SetTall(S(50))
    footer:DockMargin(0, S(10), 0, 0)
    footer.Paint = function(_, w, h)
        local village = NB.GetVillage(choice.village or "")
        local clan = NB.GetClan(choice.clan)
        local nature = NB.GetNature(choice.nature or "")
        local summary = string.format("%s  ·  %s  ·  %s",
            village and village.name or "Village ?",
            clan and clan.name or "Clan ?",
            nature and (nature.name .. " (" .. nature.desc .. ")") or "Nature ?")
        draw.SimpleText(summary, "NB.Medium", 0, h / 2, T.text, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    end

    local confirm = NB.UI.Button(footer, "Commencer l'aventure", function()
        NB.RequestCreate(choice.village, choice.clan, choice.nature)
        frame:Close()
    end, T.success)
    confirm:Dock(RIGHT)
    confirm:SetWide(S(260))
    confirm:SetEnabled(false)

    local function refreshConfirm()
        confirm:SetEnabled(choice.village ~= nil and choice.nature ~= nil and choice.clan ~= nil)
    end

    local width = (frame:GetWide() - S(24) - S(20)) / 3
    local villagePanel, villageList = column(columns, "1. Village")
    local clanPanel, clanList = column(columns, "2. Clan")
    local naturePanel, natureList = column(columns, "3. Nature de chakra")
    villagePanel:SetWide(width)
    clanPanel:SetWide(width)
    naturePanel:SetWide(width)
    naturePanel:DockMargin(0, 0, 0, 0)

    -- Sélection exclusive dans une liste de cartes
    local function selectIn(list, card)
        for _, child in ipairs(list:GetCanvas():GetChildren()) do
            child.Selected = false
        end
        card.Selected = true
    end

    local function buildClans()
        clanList:Clear()
        choice.clan = "aucun"
        for _, clan in ipairs(NB.Config.Clans) do
            if clan.village == nil or clan.village == choice.village then
                local bonus = clan.chakraMult ~= 1
                    and string.format("  (chakra +%d%%)", math.Round((clan.chakraMult - 1) * 100)) or ""
                local card = NB.UI.Card(clanList, clan.name .. bonus, clan.desc, T.accent, function(self)
                    selectIn(clanList, self)
                    choice.clan = clan.id
                    refreshConfirm()
                end)
                card.Selected = clan.id == choice.clan
            end
        end
        refreshConfirm()
    end

    for _, village in ipairs(NB.Config.Villages) do
        NB.UI.Card(villageList, village.name, village.full, village.color, function(self)
            selectIn(villageList, self)
            choice.village = village.id
            buildClans()
        end)
    end

    for _, nature in ipairs(NB.Config.Natures) do
        NB.UI.Card(natureList, nature.name, nature.desc, nature.color, function(self)
            selectIn(natureList, self)
            choice.nature = nature.id
            refreshConfirm()
        end)
    end

    buildClans()
end

concommand.Add("nb_creation", function() NB.OpenCreationMenu() end)
