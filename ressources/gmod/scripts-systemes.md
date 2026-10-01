# ⚙️ Garry's Mod – Scripts & systèmes de jeu

[← Sommaire](../README.md) · Légende : 🟢 libre · 🟡 conditions · 🔵 outil/doc · 🔴 référence seulement

Briques techniques pour construire les systèmes d'un serveur : sauvegarde, réseau, permissions, configuration, animations par le code.

> 🍥 Un exemple complet qui assemble tout ça (chakra, jutsus, rangs, villages, sauvegarde) : l'addon [**naruto_base**](../projets/naruto-rp/addons/naruto_base/README.md).

## 💾 Sauvegarder les données des joueurs

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [sql (wiki)](https://wiki.facepunch.com/gmod/sql) | Base SQLite intégrée à GMod, aucune installation | **Toujours** échapper avec `sql.SQLStr` |
| 🟢 | [gmod-sqlite-explanation](https://github.com/BullyHunter32/gmod-sqlite-explanation) | Explications et exemples SQLite | |
| 🟢 | [MySQLOO](https://github.com/FredyH/MySQLOO) | MySQL (plusieurs serveurs, site web connecté) | Requêtes asynchrones |
| 🟢 | [gConfig](https://github.com/Donkie/gConfig) | Configuration modifiable en jeu, stockée en SQL ou fichier | |

## 📡 Réseau client ⇄ serveur

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [net (wiki)](https://wiki.facepunch.com/gmod/net) · [bonnes pratiques](https://wiki.facepunch.com/gmod/Net_Library_Usage) | La librairie net | Le serveur doit **tout revérifier** |
| 🟢 | [gm_express](https://github.com/CFC-Servers/gm_express) | Gros transferts de données | |
| 🟢 | [NetStream](https://github.com/alexgrist/NetStream) | Surcouche simple | |

## 🔐 Permissions & administration

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [CAMI](https://github.com/glua/CAMI) | Interface commune aux mods d'admin (ULX, SAM, DarkRP…) | Notre addon s'en sert pour ses commandes admin |
| 🟢 | [ULX](https://github.com/TeamUlysses/ulx) + [ULib](https://github.com/TeamUlysses/ulib) | Mod d'admin | |

## 🕺 Animations par le code

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Player:AnimRestartGesture](https://wiki.facepunch.com/gmod/Player:AnimRestartGesture) | Jouer une animation de geste | **Pas synchronisé automatiquement** : à envoyer à chaque client |
| 🔵 | [Player:AddVCDSequenceToGestureSlot](https://wiki.facepunch.com/gmod/Player:AddVCDSequenceToGestureSlot) | Jouer une séquence par son nom (packs wOS/DynaBase) | Idem |
| 🔵 | [GESTURE_SLOT](https://wiki.facepunch.com/gmod/Enums/GESTURE_SLOT) | Emplacements de gestes | |
| 🔵 | [Hooks du gamemode](https://wiki.facepunch.com/gmod/GM_Hooks) | Liste de tous les hooks | |

## 🧰 Boîtes à outils de dev

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [LibK](https://github.com/Kamshak/LibK) | Bibliothèque pour développer des addons plus vite | |
| 🟢 | [gmod-holylib](https://github.com/RaphaelIT7/gmod-holylib) | Module serveur : fonctions, optimisations, correctifs | Module binaire |
| 🟢 | [GLuaFixer / glualint](https://github.com/FPtje/GLuaFixer) | Linter GLua en ligne de commande | Pour vérifier le code avant de publier |
| 🟢 | [CFC-Servers](https://github.com/CFC-Servers) | Nombreux addons open source d'un gros serveur | Bonne source d'exemples de qualité |
