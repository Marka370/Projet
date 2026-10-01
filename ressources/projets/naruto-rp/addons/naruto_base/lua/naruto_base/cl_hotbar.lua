--[[
    Naruto Base — barre de jutsus (bas de l'écran) et touches de lancement.
]]

local T = NB.Config.Theme
local S = NB.UI.Scale

function NB.CastSlot(slot)
    local id = NB.Local.slots[slot]
    if not id then
        NB.Notify(NB.L("empty_slot", NB.UI.KeyName(NB.Config.MenuKey)), "error")
        return
    end
    -- Vérification locale pour une réponse immédiate ; le serveur revérifie tout
    local ok, reason = NB.CanCast(LocalPlayer(), id)
    if not ok then
        NB.Notify(reason, "error")
        return
    end
    NB.RequestCast(id)
end

local function isTyping()
    return LocalPlayer():IsTyping() or gui.IsGameUIVisible() or IsValid(vgui.GetKeyboardFocus())
end

hook.Add("PlayerButtonDown", "NB_Hotbar", function(ply, button)
    if ply ~= LocalPlayer() or not IsFirstTimePredicted() or isTyping() then return end

    if button == NB.Config.MenuKey then
        NB.OpenJutsuMenu()
        return
    end
    for slot, key in ipairs(NB.Config.HotbarKeys) do
        if button == key then
            NB.CastSlot(slot)
            return
        end
    end
end)

-- Commandes utilisables avec « bind » si on préfère d'autres touches
concommand.Add("nb_cast_slot", function(_, _, args)
    local slot = tonumber(args[1] or "")
    if slot then NB.CastSlot(slot) end
end)
concommand.Add("nb_menu", function() NB.OpenJutsuMenu() end)

-- ───────────────────────────── Dessin

local function selectedSlot()
    local weapon = LocalPlayer():GetActiveWeapon()
    if IsValid(weapon) and weapon:GetClass() == "weapon_nb_ninja" then
        return weapon:GetJutsuSlot()
    end
end

hook.Add("HUDPaint", "NB_Hotbar", function()
    local ply = LocalPlayer()
    if not IsValid(ply) or not ply:Alive() or not ply:NB_IsCreated() then return end

    local count = #NB.Config.HotbarKeys
    local size, gap = S(68), S(8)
    local totalW = count * size + (count - 1) * gap
    local x0, y = (ScrW() - totalW) / 2, ScrH() - size - S(24)
    local chakra = ply:NB_GetChakra()
    local selected = selectedSlot()

    for slot = 1, count do
        local x = x0 + (slot - 1) * (size + gap)
        local id = NB.Local.slots[slot]
        local jutsu = id and NB.GetJutsu(id)

        draw.RoundedBox(6, x, y, size, size, T.background)

        if jutsu then
            local nature = NB.GetNature(jutsu.nature)
            local color = nature and nature.color or T.accent
            draw.RoundedBoxEx(6, x, y, size, S(5), color, true, true, false, false)

            local short = jutsu.short or jutsu.name
            draw.SimpleText(short, "NB.Tiny", x + size / 2, y + size / 2 - S(4), T.text, TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
            local costColor = chakra >= jutsu.chakra and T.chakra or T.error
            draw.SimpleText(tostring(jutsu.chakra), "NB.Tiny", x + size - S(5), y + size - S(4), costColor, TEXT_ALIGN_RIGHT, TEXT_ALIGN_BOTTOM)

            -- Recharge : voile qui descend + secondes restantes
            local left = NB.GetCooldownLeft(ply, id)
            if left > 0 and jutsu.cooldown > 0 then
                local fraction = math.Clamp(left / jutsu.cooldown, 0, 1)
                draw.RoundedBox(6, x, y, size, size * fraction, Color(0, 0, 0, 190))
                draw.SimpleText(string.format("%.1f", left), "NB.Medium", x + size / 2, y + size / 2,
                    T.text, TEXT_ALIGN_CENTER, TEXT_ALIGN_CENTER)
            end
        end

        if selected == slot then
            surface.SetDrawColor(T.accent)
            surface.DrawOutlinedRect(x, y, size, size, 2)
        end

        draw.SimpleText(NB.UI.KeyName(NB.Config.HotbarKeys[slot]), "NB.Tiny", x + S(5), y + S(8),
            T.textDim, TEXT_ALIGN_LEFT, TEXT_ALIGN_TOP)
    end
end)
