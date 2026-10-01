--[[
    Iryō Ninjutsu — soin d'un allié devant soi (ou de soi-même).
    Exemple : jutsu qui cible un joueur (NB.Util.TargetInFront).
]]

NB.RegisterJutsu({
    id = "neutre_iryo",
    name = "Iryō Ninjutsu : Shōsen",
    short = "Soin",
    description = "Ninjutsu médical : soigne l'allié en face de toi, ou toi-même si personne n'est devant.",
    nature = "neutre",
    rank = "genin",
    chakra = 30,
    cooldown = 10,
    gesture = ACT_GMOD_GESTURE_ITEM_GIVE,

    OnCast = function(ply)
        local target = NB.Util.TargetInFront(ply, 120)
        if not (IsValid(target) and target:IsPlayer()) then target = ply end

        local maxHealth = target:GetMaxHealth()
        if target:Health() >= maxHealth then
            NB.Notify(ply, "Aucune blessure à soigner.", "error")
            return false
        end
        target:SetHealth(math.min(maxHealth, target:Health() + 35))
        target:EmitSound("items/medshot4.wav", 70)
        NB.Util.Effect("cball_bounce", target:GetPos() + Vector(0, 0, 40), 1)
    end,
})
