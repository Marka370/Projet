--[[
    Raiton : Chidori — charge électrique au corps à corps.
    Exemple : jutsu en deux temps (élan, puis impact avec timer.Simple).
]]

NB.RegisterJutsu({
    id = "raiton_chidori",
    name = "Raiton : Chidori",
    short = "Chidori",
    description = "Concentre la foudre dans ta main et charge ta cible : gros dégâts électriques.",
    nature = "raiton",
    rank = "chunin",
    chakra = 50,
    cooldown = 12,
    gesture = ACT_GMOD_GESTURE_MELEE_SHOVE_1HAND,

    OnCast = function(ply)
        local direction = ply:GetAimVector()
        direction.z = 0
        direction:Normalize()
        ply:SetVelocity(direction * 700)
        ply:EmitSound("ambient/energy/zap1.wav", 85, 110)

        timer.Simple(0.25, function()
            if not IsValid(ply) or not ply:Alive() then return end
            local target, tr = NB.Util.TargetInFront(ply, 110)
            NB.Util.Effect("cball_explode", tr.HitPos, 1)
            if IsValid(target) then
                NB.Util.Damage(ply, target, 55, DMG_SHOCK, direction * 20000)
                target:EmitSound("ambient/energy/zap9.wav", 85)
            end
        end)
    end,
})
