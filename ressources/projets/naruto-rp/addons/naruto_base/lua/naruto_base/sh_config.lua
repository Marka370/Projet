--[[
    Naruto Base — CONFIGURATION
    C'est le seul fichier à modifier pour adapter l'addon à ton serveur.
]]

NB.Config = {}
local C = NB.Config

-- ───────────────────────────── Général
C.Language = "fr"
C.HideDefaultHUD = true        -- cache la vie / armure d'origine de GMod
C.SaveInterval = 120           -- sauvegarde automatique (secondes)

-- ───────────────────────────── Touches
-- Liste des touches : https://wiki.facepunch.com/gmod/Enums/KEY
C.HotbarKeys = { KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B }   -- un jutsu par touche
C.MenuKey = KEY_J                                      -- ouvre le livre des jutsus

-- ───────────────────────────── Chakra
C.ChakraRegenInterval = 0.5    -- fréquence de régénération (secondes)
C.MeditationMultiplier = 3     -- accroupi et immobile = régénération x3
C.CastRateLimit = 0.25         -- délai minimum entre deux demandes de jutsu (anti-spam)

-- ───────────────────────────── Progression
C.XPPerCast = 2                -- XP gagnée à chaque jutsu réussi
C.AutoRankUp = true            -- promotion automatique quand l'XP est atteinte
C.StartRank = "academie"

-- Rangs, du plus bas au plus haut.
-- xp = XP nécessaire pour l'obtenir automatiquement (nil = nomination par un admin)
C.Ranks = {
    { id = "academie", name = "Élève de l'Académie", maxChakra = 60,  regen = 2, xp = 0 },
    { id = "genin",    name = "Genin",               maxChakra = 100, regen = 3, xp = 100 },
    { id = "chunin",   name = "Chūnin",              maxChakra = 150, regen = 4, xp = 400 },
    { id = "jonin",    name = "Jōnin",               maxChakra = 220, regen = 5, xp = 1200 },
    { id = "anbu",     name = "ANBU",                maxChakra = 250, regen = 6, xp = nil },
    { id = "kage",     name = "Kage",                maxChakra = 350, regen = 8, xp = nil },
}

-- ───────────────────────────── Villages
C.Villages = {
    { id = "konoha", name = "Konoha", full = "Konohagakure — Village caché de la Feuille", color = Color(76, 175, 80) },
    { id = "suna",   name = "Suna",   full = "Sunagakure — Village caché du Sable",       color = Color(222, 184, 110) },
    { id = "kiri",   name = "Kiri",   full = "Kirigakure — Village caché de la Brume",    color = Color(90, 160, 220) },
    { id = "kumo",   name = "Kumo",   full = "Kumogakure — Village caché des Nuages",     color = Color(240, 214, 90) },
    { id = "iwa",    name = "Iwa",    full = "Iwagakure — Village caché de la Roche",     color = Color(160, 125, 95) },
}

-- ───────────────────────────── Natures de chakra
C.Natures = {
    { id = "katon",  name = "Katon",  desc = "Feu",    color = Color(235, 90, 40) },
    { id = "suiton", name = "Suiton", desc = "Eau",    color = Color(60, 140, 230) },
    { id = "futon",  name = "Fūton",  desc = "Vent",   color = Color(150, 220, 170) },
    { id = "raiton", name = "Raiton", desc = "Foudre", color = Color(250, 230, 80) },
    { id = "doton",  name = "Doton",  desc = "Terre",  color = Color(170, 120, 70) },
}

-- ───────────────────────────── Clans
-- village = nil : accessible depuis tous les villages
-- chakraMult : multiplicateur du chakra maximum
C.Clans = {
    { id = "aucun",   name = "Sans clan", village = nil,      chakraMult = 1.0,  desc = "Un ninja sans héritage, libre de tracer sa voie." },
    { id = "uchiha",  name = "Uchiha",    village = "konoha", chakraMult = 1.1,  desc = "Clan au Sharingan, maîtres du Katon." },
    { id = "hyuga",   name = "Hyūga",     village = "konoha", chakraMult = 1.05, desc = "Porteurs du Byakugan, experts du Jūken." },
    { id = "nara",    name = "Nara",      village = "konoha", chakraMult = 1.05, desc = "Stratèges qui manipulent les ombres." },
    { id = "senju",   name = "Senju",     village = "konoha", chakraMult = 1.2,  desc = "Clan à la vitalité et au chakra exceptionnels." },
    { id = "sabaku",  name = "Sabaku",    village = "suna",   chakraMult = 1.1,  desc = "Famille du Kazekage, liée au sable." },
    { id = "hozuki",  name = "Hōzuki",    village = "kiri",   chakraMult = 1.05, desc = "Capables de se liquéfier." },
    { id = "yotsuki", name = "Yotsuki",   village = "kumo",   chakraMult = 1.1,  desc = "Guerriers de la foudre." },
    { id = "kamizuru",name = "Kamizuru",  village = "iwa",    chakraMult = 1.05, desc = "Clan des insectes." },
}

-- ───────────────────────────── Animations
-- Geste joué par défaut quand un jutsu n'en définit pas.
-- Avec un pack wOS / DynaBase, un jutsu peut aussi indiquer « sequence = "nom_de_sequence" ».
C.DefaultGesture = ACT_GMOD_GESTURE_ITEM_PLACE

-- ───────────────────────────── Couleurs de l'interface
C.Theme = {
    background = Color(18, 18, 24, 230),
    panel      = Color(30, 30, 40, 240),
    accent     = Color(255, 140, 40),     -- orange « Naruto »
    text       = Color(240, 240, 240),
    textDim    = Color(160, 160, 170),
    health     = Color(200, 50, 60),
    chakra     = Color(60, 140, 255),
    xp         = Color(255, 200, 60),
    error      = Color(230, 70, 70),
    success    = Color(80, 200, 120),
}
