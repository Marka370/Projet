--[[
    Naruto Base — réception des données du serveur et envoi des demandes.
]]

-- Données du joueur local (copie envoyée par le serveur)
NB.Local = NB.Local or {
    created = false,
    xp = 0,
    learned = {},  -- [id] = true
    slots = {},    -- [numéro] = id
}

function NB.GetLearnedSet(ply)
    if ply == LocalPlayer() then return NB.Local.learned end
    return {}
end

-- ───────────────────────────── Réception

net.Receive("nb_sync", function()
    local payload = util.JSONToTable(net.ReadString())
    if not istable(payload) then return end

    NB.Local.created = payload.created == true
    NB.Local.xp = tonumber(payload.xp) or 0

    NB.Local.learned = {}
    for _, id in ipairs(payload.learned or {}) do
        NB.Local.learned[id] = true
    end

    NB.Local.slots = {}
    for i = 1, #NB.Config.HotbarKeys do
        local id = payload.slots and payload.slots[i]
        if isstring(id) and id ~= "" then NB.Local.slots[i] = id end
    end

    hook.Run("NB_LocalSync")

    if not NB.Local.created then
        timer.Simple(0.5, function()
            if not NB.Local.created and NB.OpenCreationMenu then NB.OpenCreationMenu() end
        end)
    end
end)

net.Receive("nb_cooldown", function()
    local id = net.ReadString()
    local endTime = net.ReadFloat()
    NB.SetCooldownEnd(LocalPlayer(), id, endTime)
end)

net.Receive("nb_gesture", function()
    local ply = net.ReadEntity()
    local act = net.ReadUInt(16)
    local sequence = net.ReadString()
    if not IsValid(ply) or not ply:IsPlayer() then return end

    -- Séquence nommée (packs wOS / DynaBase) si le modèle la possède
    if sequence ~= "" then
        local seq = ply:LookupSequence(sequence)
        if seq and seq > 0 then
            ply:AddVCDSequenceToGestureSlot(GESTURE_SLOT_CUSTOM, seq, 0, true)
            return
        end
    end
    if act > 0 then
        ply:AnimRestartGesture(GESTURE_SLOT_CUSTOM, act, true)
    end
end)

-- ───────────────────────────── Envoi

function NB.RequestCast(id)
    net.Start("nb_cast")
    net.WriteString(id)
    net.SendToServer()
end

function NB.RequestSetSlot(slot, id)
    net.Start("nb_setslot")
    net.WriteUInt(slot, 4)
    net.WriteString(id or "")
    net.SendToServer()
end

function NB.RequestCreate(village, clan, nature)
    net.Start("nb_create")
    net.WriteString(village)
    net.WriteString(clan)
    net.WriteString(nature)
    net.SendToServer()
end

-- Le serveur n'envoie les données qu'une fois le client prêt
local function sendReady()
    net.Start("nb_ready")
    net.SendToServer()
end
hook.Add("InitPostEntity", "NB_Ready", sendReady)
if IsValid(LocalPlayer()) then sendReady() end -- rechargement du Lua en jeu
