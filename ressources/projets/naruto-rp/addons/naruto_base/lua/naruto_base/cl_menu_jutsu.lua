--[[
    Naruto Base — livre des jutsus : liste des techniques, détails,
    et placement dans la barre (touche J par défaut, commande : nb_menu).
]]

local T = NB.Config.Theme
local S = NB.UI.Scale

local frame

local REQUIREMENT_TEXT = {
    rank = "Rang insuffisant",
    nature = "Mauvaise nature de chakra",
    clan = "Réservé à un clan",
    village = "Réservé à un village",
}

local function statusOf(ply, jutsu)
    if NB.KnowsJutsu(ply, jutsu.id) then return true, "Connue" end
    local _, missing = NB.MeetsRequirements(ply, jutsu)
    if missing then return false, REQUIREMENT_TEXT[missing] or "Verrouillée" end
    return false, "À apprendre auprès d'un maître"
end

function NB.OpenJutsuMenu()
    local ply = LocalPlayer()
    if not ply:NB_IsCreated() then
        NB.OpenCreationMenu()
        return
    end
    if IsValid(frame) then
        frame:Close()
        return
    end

    frame = NB.UI.Frame("Livre des jutsus", 980, 620)
    local selected

    -- ── Colonne de gauche : liste
    local listPanel = vgui.Create("DScrollPanel", frame)
    listPanel:Dock(LEFT)
    listPanel:SetWide(S(380))
    listPanel:DockMargin(0, 0, S(12), 0)

    -- ── Colonne de droite : détails
    local details = vgui.Create("DPanel", frame)
    details:Dock(FILL)
    details:DockPadding(S(16), S(16), S(16), S(16))

    local buttons = vgui.Create("DPanel", details)
    buttons:Dock(BOTTOM)
    buttons:SetTall(S(92))
    buttons.Paint = nil

    local description = vgui.Create("DLabel", details)
    description:SetFont("NB.Small")
    description:SetTextColor(T.text)
    description:SetWrap(true)
    description:SetContentAlignment(7)
    description:Dock(FILL)
    description:DockMargin(0, S(150), 0, S(10))
    description:SetText("")

    details.Paint = function(_, w, h)
        draw.RoundedBox(6, 0, 0, w, h, Color(0, 0, 0, 90))
        if not selected then
            draw.SimpleText("Choisis une technique à gauche", "NB.Medium", w / 2, h / 2, T.textDim,
                TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
            return
        end
        local nature = NB.GetNature(selected.nature)
        local natureName = nature and (nature.name .. " — " .. nature.desc) or "Neutre"
        local known, status = statusOf(ply, selected)

        draw.SimpleText(selected.name, "NB.Large", S(16), S(30), T.text, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
        draw.SimpleText(natureName, "NB.Small", S(16), S(62), nature and nature.color or T.textDim,
            TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
        draw.SimpleText(string.format("Chakra : %d     Recharge : %s s     Rang : %s",
            selected.chakra, selected.cooldown, NB.GetRank(selected.rank).name),
            "NB.Small", S(16), S(92), T.textDim, TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
        draw.SimpleText(status, "NB.Small", S(16), S(122), known and T.success or T.error,
            TEXT_ALIGN_LEFT, TEXT_ALIGN_CENTER)
    end

    local function rebuildButtons()
        buttons:Clear()
        if not selected then return end
        local known = NB.KnowsJutsu(ply, selected.id)
        local count = #NB.Config.HotbarKeys
        local width = (details:GetWide() - S(32) - (count - 1) * S(6)) / count

        local label = vgui.Create("DLabel", buttons)
        label:Dock(TOP)
        label:SetFont("NB.Small")
        label:SetTextColor(T.textDim)
        label:SetText(known and "Placer dans la barre :" or "Technique pas encore connue")
        label:SetTall(S(26))

        for slot = 1, count do
            local current = NB.Local.slots[slot]
            local isHere = current == selected.id
            local text = NB.UI.KeyName(NB.Config.HotbarKeys[slot]) .. (isHere and "  ✓" or "")
            local button = NB.UI.Button(buttons, text, function()
                -- Re-cliquer sur l'emplacement actuel retire le jutsu
                NB.RequestSetSlot(slot, isHere and "" or selected.id)
            end, isHere and T.success or nil)
            button:Dock(LEFT)
            button:SetWide(width)
            button:DockMargin(0, S(8), slot < count and S(6) or 0, 0)
            button:SetEnabled(known)
        end
    end

    local function select(jutsu)
        selected = jutsu
        description:SetText(jutsu.description)
        rebuildButtons()
    end

    local function buildList()
        listPanel:Clear()
        for _, jutsu in ipairs(NB.GetSortedJutsus()) do
            local known, status = statusOf(ply, jutsu)
            local nature = NB.GetNature(jutsu.nature)
            local row = NB.UI.Card(listPanel, jutsu.name,
                string.format("%s  ·  %d chakra  ·  %s", status, jutsu.chakra, NB.GetRank(jutsu.rank).name),
                known and (nature and nature.color or T.accent) or Color(80, 80, 90),
                function(self)
                    for _, child in ipairs(listPanel:GetCanvas():GetChildren()) do child.Selected = false end
                    self.Selected = true
                    select(jutsu)
                end)
            row:SetAlpha(known and 255 or 140)
            row.Selected = selected ~= nil and selected.id == jutsu.id
        end
    end

    buildList()

    -- Le serveur a confirmé un changement : on rafraîchit
    hook.Add("NB_LocalSync", "NB_JutsuMenu", function()
        if not IsValid(frame) then
            hook.Remove("NB_LocalSync", "NB_JutsuMenu")
            return
        end
        buildList()
        rebuildButtons()
    end)
end
