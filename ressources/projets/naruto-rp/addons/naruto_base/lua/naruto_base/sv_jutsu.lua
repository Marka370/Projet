--[[
    Naruto Base — lancement des jutsus côté serveur.
]]

-- Joue une animation sur un joueur, visible par tous.
-- act : ACT_* (geste standard) ; sequence : nom de séquence (packs wOS / DynaBase)
function NB.PlayGesture(ply, act, sequence)
    net.Start("nb_gesture")
    net.WriteEntity(ply)
    net.WriteUInt(act or 0, 16)
    net.WriteString(sequence or "")
    net.Broadcast()
end

-- Point d'entrée unique pour lancer un jutsu (touches, arme, commandes…)
function NB.TryCast(ply, id)
    local ok, reason = NB.CanCast(ply, id)
    if not ok then
        NB.Notify(ply, reason, "error")
        return false
    end

    local jutsu = NB.GetJutsu(id)
    if hook.Run("NB_CanCastJutsu", ply, id) == false then return false end

    local success, result = pcall(jutsu.OnCast, ply, jutsu)
    if not success then
        NB.Log("Erreur dans le jutsu « " .. id .. " » : " .. tostring(result))
        NB.Notify(ply, NB.L("cast_failed"), "error")
        return false
    end
    if result == false then
        -- Le jutsu a refusé (pas de cible…) : pas de coût ni de cooldown
        return false
    end

    NB.SetChakra(ply, ply:NB_GetChakra() - jutsu.chakra)

    local endTime = CurTime() + jutsu.cooldown
    NB.SetCooldownEnd(ply, id, endTime)
    net.Start("nb_cooldown")
    net.WriteString(id)
    net.WriteFloat(endTime)
    net.Send(ply)

    NB.PlayGesture(ply, jutsu.gesture or NB.Config.DefaultGesture, jutsu.sequence)
    NB.AddXP(ply, jutsu.xp or NB.Config.XPPerCast)
    hook.Run("NB_JutsuCast", ply, id)
    return true
end

-- Jutsu placé dans un emplacement de la barre
function NB.GetSlotJutsu(ply, slot)
    local data = NB.Data[ply]
    return data and data.slots[slot] or nil
end

net.Receive("nb_cast", function(_, ply)
    if NB.IsRateLimited(ply, "cast", NB.Config.CastRateLimit) then return end
    local id = net.ReadString()
    if #id > 64 then return end
    NB.TryCast(ply, id)
end)
