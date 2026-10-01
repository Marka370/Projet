--[[
    Naruto Base — textes affichés aux joueurs.
    Pour traduire : ajoute NB.Lang.en = { ... } et mets NB.Config.Language = "en".
]]

NB.Lang = NB.Lang or {}

NB.Lang.fr = {
    -- Jutsus
    unknown_jutsu    = "Technique inconnue.",
    not_learned      = "Tu ne connais pas cette technique.",
    not_created      = "Crée d'abord ton personnage.",
    dead             = "Impossible quand on est mort.",
    no_chakra        = "Pas assez de chakra !",
    cooldown         = "Technique en recharge (%s s).",
    cast_failed      = "La technique a échoué.",
    no_target        = "Aucune cible devant toi.",
    empty_slot       = "Aucun jutsu dans cet emplacement (touche %s pour ouvrir le livre).",
    slot_selected    = "Emplacement %d : %s",

    -- Progression
    rank_up          = "Promotion ! Tu es maintenant %s.",
    jutsu_learned    = "Nouvelle technique apprise : %s",

    -- Création de personnage
    created          = "Bienvenue, ninja de %s !",
    already_created  = "Ton personnage existe déjà.",
    invalid_choice   = "Choix invalide.",

    -- Admin
    no_permission    = "Tu n'as pas la permission.",
    player_not_found = "Joueur introuvable.",
    done             = "C'est fait.",
}

function NB.L(key, ...)
    local lang = NB.Lang[NB.Config.Language] or NB.Lang.fr
    local text = lang[key] or NB.Lang.fr[key] or key
    if select("#", ...) > 0 then
        return string.format(text, ...)
    end
    return text
end
