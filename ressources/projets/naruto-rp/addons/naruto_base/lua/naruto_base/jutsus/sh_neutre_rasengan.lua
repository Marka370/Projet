--[[
    Rasengan — sphère de chakra qui projette la cible.
    Exemple : jutsu réservé à un rang élevé et projection (SetVelocity).
]]

NB.RegisterJutsu({
    id = "neutre_rasengan",
    name = "Rasengan",
    short = "Rasengan",
    description = "Une sphère de chakra en rotation qui projette violemment la cible.",
    nature = "neutre",
    rank = "jonin",
    chakra = 60,
    cooldown = 15,
    gesture = ACT_GMOD_GESTURE_MELEE_SHOVE_1HAND,

    OnCast = function(ply)
        local target, tr = NB.Util.TargetInFront(ply, 100)
        if not IsValid(target) then
            NB.Notify(ply, NB.L("no_target"), "error")
            return false
        end
        local direction = ply:GetAimVector()
        NB.Util.Effect("cball_explode", tr.HitPos, 2)
        NB.Util.Damage(ply, target, 60, DMG_BLAST, direction * 40000)
        target:SetVelocity(direction * 700 + Vector(0, 0, 300))
        target:EmitSound("weapons/physcannon/energy_sing_explosion2.wav", 85)
    end,
})
