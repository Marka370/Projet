--[[
    Shunshin no Jutsu — déplacement éclair vers l'avant.
    Exemple le plus simple : modifier la vitesse du joueur + un effet.
]]

NB.RegisterJutsu({
    id = "neutre_shunshin",
    name = "Shunshin no Jutsu",
    short = "Shunshin",
    description = "Déplacement instantané : tu fonces vers l'avant dans un nuage de fumée.",
    nature = "neutre",
    rank = "academie",
    chakra = 10,
    cooldown = 3,
    gesture = ACT_GMOD_GESTURE_ITEM_PLACE,

    OnCast = function(ply)
        local direction = ply:GetAimVector()
        direction.z = math.max(direction.z, 0.1)
        NB.Util.Effect("ThumperDust", ply:GetPos(), 1)
        ply:SetVelocity(direction * 900 + Vector(0, 0, 180))
        ply:EmitSound("npc/zombie/claw_miss1.wav", 70, 140)
    end,
})
