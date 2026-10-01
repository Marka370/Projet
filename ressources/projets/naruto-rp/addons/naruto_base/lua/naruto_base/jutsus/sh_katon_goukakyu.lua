--[[
    Katon : Gōkakyū no Jutsu — grande boule de feu.
    Exemple : jutsu qui crée une entité (lua/entities/nb_fireball.lua).
]]

NB.RegisterJutsu({
    id = "katon_goukakyu",
    name = "Katon : Gōkakyū no Jutsu",
    short = "Gōkakyū",
    description = "Crache une énorme boule de feu qui explose à l'impact et enflamme les ennemis proches.",
    nature = "katon",
    rank = "genin",
    chakra = 35,
    cooldown = 6,
    gesture = ACT_GMOD_GESTURE_ITEM_THROW,

    OnCast = function(ply)
        local fireball = ents.Create("nb_fireball")
        if not IsValid(fireball) then return false end
        local direction = ply:GetAimVector()
        fireball:SetPos(ply:EyePos() + direction * 40)
        fireball:SetOwner(ply)
        fireball:Spawn()
        fireball:Launch(direction, 1100)
        ply:EmitSound("ambient/fire/ignite.wav", 80, 90)
    end,
})
