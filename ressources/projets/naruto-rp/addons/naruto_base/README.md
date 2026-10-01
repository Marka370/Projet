# 🍥 Naruto Base — addon Garry's Mod

Base de départ **open source** pour un serveur Naruto RP. C'est notre propre code : on peut le modifier, le partager et le publier librement.

| Système | Ce qui est inclus |
|---|---|
| 🧑 **Création de personnage** | Menu au premier lancement : 5 villages, 9 clans (bonus de chakra), 5 natures de chakra |
| 🔵 **Chakra** | Jauge synchronisée, régénération selon le rang, **méditation** (accroupi et immobile = x3) |
| 🥷 **Jutsus** | Système complet : coût en chakra, temps de recharge, rang, nature, clan ou village requis, animations |
| ⌨️ **Barre de jutsus** | 5 emplacements (touches **Z X C V B**), affichage du coût et de la recharge |
| 📖 **Livre des jutsus** | Menu (touche **J**) : liste, conditions, détails, placement dans la barre |
| 📈 **Progression** | XP à chaque jutsu, promotion automatique Académie → Genin → Chūnin → Jōnin ; ANBU et Kage nommés par un admin |
| 🖥️ **HUD** | Nom, village, rang, clan, nature, vie, chakra, progression ; notifications à l'écran |
| ✋ **Arme « Mains de ninja »** | Clic gauche : jutsu · clic droit : changer d'emplacement · R : livre des jutsus |
| 💾 **Sauvegarde** | SQLite intégré (aucune installation), sauvegarde auto + à la déconnexion |
| 🛡️ **Admin** | Commandes console et chat, compatibles ULX / SAM / DarkRP via CAMI |
| 🔒 **Sécurité** | Le serveur revérifie tout, anti-spam des messages, données corrompues nettoyées |

**6 jutsus d'exemple**, chacun montrant une technique de code différente :

| Jutsu | Rang | Ce que montre son code |
|---|---|---|
| Shunshin no Jutsu | Académie | Le plus simple : propulser le joueur |
| Kawarimi no Jutsu | Académie | Téléportation sûre (vérifie qu'il y a de la place) + objet temporaire |
| Iryō Ninjutsu | Genin | Cibler un allié, refuser sans coût si inutile |
| Katon : Gōkakyū | Genin (Katon) | Projectile (entité `nb_fireball`) : explosion, brûlure, lumière |
| Raiton : Chidori | Chūnin (Raiton) | Jutsu en deux temps (élan puis impact) |
| Rasengan | Jōnin | Dégâts + projection de la cible |

---

## 📥 Installation

1. Télécharge le dossier `naruto_base` :
   - soit l'archive prête à l'emploi dans l'onglet **Actions › Addon Naruto Base › (dernière exécution) › Artifacts** ;
   - soit le dépôt entier (**Code › Download ZIP**).
2. Copie le dossier `naruto_base` dans `garrysmod/addons/` sur ton serveur (ou ton jeu, pour tester en solo).
3. Redémarre la map. Au premier lancement, le menu de création s'ouvre.

> Pour tester seul : lance une partie en **multijoueur local** (pas solo), sinon certains comportements réseau diffèrent.

## 🎮 Commandes

| Joueurs | |
|---|---|
| `J` | Livre des jutsus |
| `Z` `X` `C` `V` `B` | Lancer le jutsu de l'emplacement 1 à 5 |
| `nb_menu` / `nb_creation` | Ouvrir les menus depuis la console |
| `bind <touche> "nb_cast_slot 1"` | Mettre un emplacement sur une autre touche |

| Admins (console ou chat avec `!`) | |
|---|---|
| `nb_setrank <joueur> <rang>` | ex. `!nb_setrank Naruto chunin` |
| `nb_givejutsu <joueur> <id>` | Apprendre un jutsu à quelqu'un |
| `nb_setxp <joueur> <xp>` | Fixer l'XP |
| `nb_chakra [joueur]` | Remplir le chakra |
| `nb_reset <joueur>` | Le joueur recrée son personnage |
| `nb_list` | Liste des rangs, villages et jutsus |

## ⚙️ Personnaliser

Tout se règle dans **`lua/naruto_base/sh_config.lua`** : touches, rangs (chakra, régénération, XP), villages, clans, natures, couleurs de l'interface. Les textes sont dans `sh_lang.lua`.

## ➕ Créer un jutsu

Crée un fichier dans `lua/naruto_base/jutsus/`, par ex. `sh_suiton_suijinheki.lua` (le préfixe `sh_` est obligatoire) :

```lua
NB.RegisterJutsu({
    id = "suiton_suijinheki",            -- identifiant unique (sans espace)
    name = "Suiton : Suijinheki",        -- nom affiché
    short = "Suijinheki",                -- nom court pour la barre (optionnel)
    description = "Un mur d'eau te protège.",
    nature = "suiton",                   -- katon, suiton, futon, raiton, doton ou "neutre"
    rank = "chunin",                     -- rang minimum
    chakra = 40,                         -- coût
    cooldown = 10,                       -- recharge en secondes
    gesture = ACT_GMOD_GESTURE_ITEM_PLACE, -- animation (optionnel)
    -- sequence = "naruto_handsign",     -- séquence d'un pack wOS/DynaBase (optionnel)
    -- clan = "uchiha",                  -- réservé à un clan (optionnel)
    -- village = "kiri",                 -- réservé à un village (optionnel)
    -- auto = false,                     -- doit être appris (nb_givejutsu / ton propre système)

    OnCast = function(ply, jutsu)
        -- Code exécuté sur le serveur quand le jutsu est lancé.
        -- return false = annulé (pas de coût ni de recharge).
        NB.Util.Effect("WaterSplash", ply:GetPos(), 3)
    end,
})
```

Outils disponibles dans `OnCast` :

| Fonction | Rôle |
|---|---|
| `NB.Util.TargetInFront(ply, distance)` | Joueur/PNJ visé (ou `nil`) + résultat de la trace |
| `NB.Util.TraceFront(ply, distance, taille)` | Trace devant le joueur |
| `NB.Util.Damage(attaquant, cible, dégâts, type, force)` | Dégâts attribués au lanceur |
| `NB.Util.Effect(nom, position, échelle)` | Effet visuel ([liste des effets](https://wiki.facepunch.com/gmod/Default_Effects)) |
| `NB.Notify(ply, texte, "info"/"success"/"error")` | Message à l'écran |

## 🔌 Pour aller plus loin (hooks)

```lua
hook.Add("NB_CanCastJutsu", "MonAddon", function(ply, id)
    if ply:GetNW2Bool("enferme") then return false end -- bloquer un jutsu
end)
hook.Add("NB_JutsuCast", "MonAddon", function(ply, id) end)        -- après un jutsu
hook.Add("NB_RankChanged", "MonAddon", function(ply, rankId) end)   -- promotion
hook.Add("NB_CharacterCreated", "MonAddon", function(ply) end)      -- nouveau ninja
```

Fonctions serveur utiles : `NB.SetRank`, `NB.AddXP`, `NB.LearnJutsu`, `NB.SetChakra`, `NB.TryCast`, `NB.ResetPlayer`.
Infos joueur (serveur et client) : `ply:NB_GetChakra()`, `NB_GetMaxChakra()`, `NB_GetRank()`, `NB_GetVillage()`, `NB_GetClan()`, `NB_GetNature()`, `NB_IsCreated()`.

## 🗂️ Organisation du code

```
lua/
├── autorun/sh_naruto_base.lua   chargeur (sh_ = partagé, sv_ = serveur, cl_ = client)
├── naruto_base/
│   ├── sh_config.lua            ⚙️ configuration
│   ├── sh_lang.lua              textes
│   ├── sh_core.lua              recherches dans la config, infos joueur
│   ├── sh_jutsu.lua             registre des jutsus, règles, outils
│   ├── sv_data.lua              sauvegarde SQLite
│   ├── sv_player.lua            joueurs, chakra, XP, création, réseau
│   ├── sv_jutsu.lua             lancement des jutsus, animations
│   ├── sv_commands.lua          commandes admin (CAMI)
│   ├── cl_theme.lua             polices, couleurs, composants d'interface
│   ├── cl_net.lua               réception des données
│   ├── cl_notify.lua            notifications
│   ├── cl_hud.lua               HUD
│   ├── cl_hotbar.lua            barre de jutsus + touches
│   ├── cl_menu_creation.lua     menu de création
│   ├── cl_menu_jutsu.lua        livre des jutsus
│   └── jutsus/                  un fichier par jutsu
├── entities/nb_fireball.lua     projectile boule de feu
└── weapons/weapon_nb_ninja.lua  arme « Mains de ninja »
```

## ✅ Tests

La logique serveur (création, chakra, jutsus, recharges, XP, sauvegarde, sécurité, commandes admin) est testée automatiquement en dehors du jeu avec une simulation de l'API GMod (`tests/test_naruto_base.py` à la racine du dépôt). La syntaxe de **tous** les fichiers est aussi vérifiée.

⚠️ Les **interfaces** (HUD, menus) et les **effets visuels** ne peuvent être vérifiés qu'en jeu : signale tout souci d'affichage pour qu'on l'ajuste.
