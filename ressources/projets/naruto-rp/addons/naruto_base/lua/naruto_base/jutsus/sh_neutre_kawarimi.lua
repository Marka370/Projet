--[[
    Kawarimi no Jutsu — permutation : un rondin prend ta place et tu
    réapparais un peu plus loin en arrière.
    Exemple : vérifier l'espace libre avant de téléporter (TraceHull).
]]

local DISTANCE = 280

NB.RegisterJutsu({
    id = "neutre_kawarimi",
    name = "Kawarimi no Jutsu",
    short = "Kawarimi",
    description = "Permutation : un rondin prend ta place pendant que tu réapparais en arrière.",
    nature = "neutre",
    rank = "academie",
    chakra = 15,
    cooldown = 8,
    gesture = ACT_GMOD_GESTURE_ITEM_PLACE,

    OnCast = function(ply)
        local origin = ply:GetPos()
        local back = -ply:GetAimVector()
        back.z = 0
        back:Normalize()

        -- Cherche une position libre derrière le joueur
        local tr = util.TraceHull({
            start = origin + Vector(0, 0, 4),
            endpos = origin + Vector(0, 0, 4) + back * DISTANCE,
            mins = ply:OBBMins(),
            maxs = ply:OBBMaxs(),
            filter = ply,
            mask = MASK_PLAYERSOLID,
        })
        if tr.Fraction < 0.25 then
            NB.Notify(ply, "Pas assez de place derrière toi.", "error")
            return false -- pas de coût ni de recharge
        end

        -- Le « rondin » qui reste à l'ancienne place
        local log = ents.Create("prop_physics")
        if IsValid(log) then
            log:SetModel("models/props_junk/wood_crate001a.mdl")
            log:SetPos(origin + Vector(0, 0, 20))
            log:Spawn()
            log:SetCollisionGroup(COLLISION_GROUP_DEBRIS)
            SafeRemoveEntityDelayed(log, 3)
        end

        NB.Util.Effect("ThumperDust", origin, 1)
        ply:SetPos(tr.HitPos - Vector(0, 0, 4))
        NB.Util.Effect("ThumperDust", ply:GetPos(), 1)
        ply:EmitSound("physics/wood/wood_crate_impact_hard2.wav", 70)
    end,
})
