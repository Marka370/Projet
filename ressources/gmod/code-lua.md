# 🧑‍💻 Garry's Mod – Code Lua (GLua)

[← Sommaire](../README.md) · Légende : 🟢 libre · 🟡 conditions · 🔵 outil/doc · 🔴 référence seulement

## 📖 Documentation officielle

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Wiki Garry's Mod](https://wiki.facepunch.com/gmod) | **La référence** : toute l'API Lua, les hooks, les tutoriels | Maintenu par Facepunch + la communauté |
| 🔵 | [Wiki – Débuter en Lua](https://wiki.facepunch.com/gmod/Beginner_Tutorial_Intro) | Tutoriel de départ officiel | |
| 🔵 | [Wiki – Utiliser la librairie net](https://wiki.facepunch.com/gmod/Net_Library_Usage) | Communication client ⇄ serveur | À lire absolument (sécurité) |
| 🟢 | [Facepunch/garrysmod](https://github.com/Facepunch/garrysmod) | Le code Lua de base du jeu (gamemode `base`, `sandbox`…) | Idéal pour comprendre comment le jeu marche. Ex. : [animations.lua](https://github.com/Facepunch/garrysmod/blob/master/garrysmod/gamemodes/base/gamemode/animations.lua) |
| 🔵 | [Valve Developer Community – Garry's Mod](https://developer.valvesoftware.com/wiki/Garrys_Mod_Community) | Doc du moteur Source | |

## ⌨️ Éditeur de code (VS Code)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [gmod-glua-ls](https://github.com/Pollux12/gmod-glua-ls) · [extension VS Code](https://marketplace.visualstudio.com/items?itemName=Pollux.gmod-glua-ls) | Serveur de langage complet : autocomplétion, erreurs, formatage, débogueur | Le plus complet actuellement |
| 🟢 | [GLua Enhanced](https://github.com/WilliamVenner/vscode-glua-enhanced) | Autocomplétion, intégration du wiki, snippets | |
| 🟢 | [vscode-glualint](https://github.com/goz3rr/vscode-glualint) | Détecte les erreurs et formate le code (glualint) | |

## 🏛️ Frameworks / gamemodes de base

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [Helix](https://github.com/NebulousCloud/helix) · [doc](https://docs.gethelix.co/manual/getting-started/) | **Framework RP open source** : personnages, inventaire, factions, plugins | Très bonne base pour un RP « sérieux » (Naruto RP) |
| 🟢 | [DarkRP](https://github.com/FPtje/DarkRP) | Le gamemode RP le plus utilisé | Énorme écosystème d'addons |
| 🟢 | [gmod-templates (TomDotBat)](https://github.com/TomDotBat/gmod-templates) | Modèles de SWEP, entités, etc. | Base pour coder des **jutsus en SWEP** |

## 📦 Bibliothèques utiles

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [pixel-ui](https://github.com/TomDotBat/pixel-ui) | Interface (menus, HUD) moderne et rapide, remplace Derma | |
| 🟢 | [DermaWind](https://github.com/Zak2801/DermaWind) | Styliser Derma façon Tailwind CSS | |
| 🟢 | [gm_express](https://github.com/CFC-Servers/gm_express) | Envoyer de grosses données client ⇄ serveur (~100 Mo) sans bloquer le jeu | |
| 🟢 | [NetStream](https://github.com/alexgrist/NetStream) | Surcouche simple de la librairie net | |
| 🟢 | [MySQLOO](https://github.com/FredyH/MySQLOO) | Connexion à une base MySQL (sauvegarde des joueurs) | Module binaire à installer sur le serveur |
| 🟢 | [Small-GLua-Things](https://github.com/Be1zebub/Small-GLua-Things) | Plein de petits snippets et librairies | |
| 🔵 | [Topic GitHub « glua-library »](https://github.com/topics/glua-library) · [« glua »](https://github.com/topics/glua) · [« garrys-mod »](https://github.com/topics/garrys-mod) | Pour découvrir d'autres projets | |

## 🎬 Animations par le code

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [JetBoom/animationsapi](https://github.com/JetBoom/animationsapi) | Animations stockées en tables Lua (sans compiler de modèle) | |
| 🟢 | [buu342/GMod-BlenderLuaAnimationsAPIExport](https://github.com/buu342/GMod-BlenderLuaAnimationsAPIExport) | Exporte une animation Blender vers l'API ci-dessus | |

## 🛡️ Administration & permissions

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [ULX](https://github.com/TeamUlysses/ulx) + [ULib](https://github.com/TeamUlysses/ulib) | Mod d'administration classique (rangs, kick, ban…) | Compatible CAMI |

## 🔒 Sécurité (important !)

Les addons piochés au hasard peuvent contenir des **backdoors** qui donnent le contrôle du serveur à un inconnu. Scanne tout addon avant de l'installer.

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [Backdoor Shield](https://github.com/Xalalau/backdoor-shield) | Protection + scanner de fichiers | |
| 🟢 | [nomalua](https://github.com/THABBuzzkill/nomalua) | Scanner de code malveillant | |
| 🟢 | [exploitscan](https://github.com/JustPlayerDE/exploitscan) | Repère les messages net exploitables | |
| 🔵 | [Wiki – librairie net](https://wiki.facepunch.com/gmod/Net_Library_Usage) | Toujours vérifier côté serveur ce qu'envoie un client | Ne **jamais** faire `RunString` sur des données reçues |

## 🚀 Publier sur le Workshop

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Wiki – Créer un addon Workshop](https://wiki.facepunch.com/gmod/Workshop_Addon_Creation) | gmad + gmpublish, procédure officielle | |
| 🟢 | [gmpublisher](https://github.com/WilliamVenner/gmpublisher) | Appli graphique pour publier sur le Workshop | |
| 🟢 | [gmod-upload (GitHub Action)](https://github.com/vurvdev/gmod-upload) | Publier automatiquement depuis GitHub | |
| 🟢 | [Action « Gmod Steam Workshop »](https://github.com/marketplace/actions/gmod-steam-workshop) | Autre action de publication automatique | Runner Windows |
