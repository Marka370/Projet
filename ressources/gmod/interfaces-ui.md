# 🖼️ Garry's Mod – Interfaces (HUD, menus, UI)

[← Sommaire](../README.md) · Légende : 🟢 libre · 🟡 conditions · 🔵 outil/doc · 🔴 référence seulement

> 🍥 Exemple complet prêt à l'emploi : le HUD, la barre de jutsus et les menus de notre addon [**naruto_base**](../projets/naruto-rp/addons/naruto_base/README.md).

## 📖 Bases (wiki officiel)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Derma Basic Guide](https://wiki.facepunch.com/gmod/Derma_Basic_Guide) | Créer fenêtres, boutons, listes | Point de départ |
| 🔵 | [draw](https://wiki.facepunch.com/gmod/draw) · [draw.RoundedBox](https://wiki.facepunch.com/gmod/draw.RoundedBox) · [draw.RoundedBoxEx](https://wiki.facepunch.com/gmod/draw.RoundedBoxEx) | Dessiner rectangles, textes | |
| 🔵 | [Derma_DrawBackgroundBlur](https://wiki.facepunch.com/gmod/Global.Derma_DrawBackgroundBlur) | Flou d'arrière-plan pour les menus | |
| 🔵 | [render.SetScissorRect](https://wiki.facepunch.com/gmod/render.SetScissorRect) | Découper une zone de dessin (barres, jauges) | |
| 🔵 | [Material Parameters](https://wiki.facepunch.com/gmod/Material_Parameters) | `smooth`, `mips`… pour des icônes nettes | |
| 🔵 | [notification.AddLegacy](https://wiki.facepunch.com/gmod/notification.AddLegacy) | Notifications intégrées | |
| 🟢 | [Code de Derma (Facepunch)](https://github.com/Facepunch/garrysmod/tree/master/garrysmod/lua/vgui) | Le code source de tous les composants | Pour comprendre / imiter |
| 🟢 | [derma_utils.lua](https://github.com/Facepunch/garrysmod/blob/master/garrysmod/lua/derma/derma_utils.lua) | Fonctions utilitaires officielles (dont le flou) | |

## 🎨 Bibliothèques d'interface

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [pixel-ui](https://github.com/TomDotBat/pixel-ui) | UI moderne et optimisée qui remplace Derma | Très utilisée |
| 🟢 | [pulsar-ui](https://github.com/Pulsar-Dev/pulsar-ui) | Fork de pixel-ui | |
| 🟢 | [DermaWind](https://github.com/Zak2801/DermaWind) | Styliser Derma avec des classes façon Tailwind | |
| 🟢 | [RNDX](https://github.com/Srlion/RNDX) | Formes arrondies et cercles **anti-aliasés** par shader | Pour une UI très propre |
| 🟢 | [Rounded-Poly-Box](https://github.com/Goofus98/Rounded-Poly-Box) | Boîtes et bordures arrondies en polygones | |
| 🟢 | [Rectangle arrondi creux (gist)](https://gist.github.com/sn-0w/fe0d38695e83b4e758e6a79862c804f9) | Contour arrondi | |
| 🟢 | [Menu radial (gist)](https://gist.github.com/azzen/261f8e627108047fad10ff291cf09c68) | Menu circulaire | Idéal pour **choisir un jutsu** |

## 🌐 Interfaces dans le monde 3D (3D2D)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [ui3d2d](https://github.com/TomDotBat/ui3d2d) | Interfaces cliquables dans le monde (PNJ, panneaux de mission) | |
| 🟢 | [imgui 3D2D (wyozi)](https://github.com/wyozi-gmod/imgui) | UI 3D2D en mode immédiat | |
| 🟢 | [3d2d-vgui](https://github.com/handsomematt/3d2d-vgui) | Afficher des panneaux Derma dans le monde | |
| 🟢 | [gmod-3d2d-clipping](https://github.com/WilliamVenner/gmod-3d2d-clipping) | Découpage propre de l'UI 3D2D | |

## 🧩 HUD open source (exemples à étudier)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [Aykii_HUD](https://github.com/Aykiiro/Aykii_HUD) | **HUD Naruto RP** (DarkRP) | Exemple dans le thème |
| 🟢 | [MAX HUD](https://github.com/Lightdistrict/hud) | HUD minimaliste DarkRP | |
| 🟢 | [TR HUD](https://github.com/TheRollmops/tr_hud) | Vie, armure, métier, agenda | |
| 🟢 | [simpleHud](https://github.com/CMAULTOP/simpleHud) | HUD simple | MIT |
| 🟢 | [CleanHUD](https://github.com/LonelyWolf-GitHub/CleanHUD) | HUD transparent épuré | |
| 🟢 | [s_priselhud](https://github.com/frenchneo/s_priselhud) | HUD DarkRP gratuit | Auteur français |
| 🔵 | [Topic GitHub « gmod-hud »](https://github.com/topics/gmod-hud) | D'autres HUD | |

## 📋 Menus (F4, scoreboard, menu principal)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [MAX F4 Menu](https://github.com/Lightdistrict/f4menu) | Menu F4 DarkRP complet (métiers, entités, armes, liens Discord) | |
| 🟢 | [F4-GMOD](https://github.com/RopLeRm8/F4-GMOD) | F4 DarkRP configurable, 7 onglets | |
| 🟢 | [gmod-lua-menu](https://github.com/robotboy655/gmod-lua-menu) · [glua-menu](https://github.com/GIGte/glua-menu) | Menu principal du jeu réécrit en Lua | |

## 🎒 Inventaires & personnages

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔵 | [Grid-Based Inventory System (wiki)](https://wiki.facepunch.com/gmod/Grid-Based_Inventory_System) | Tutoriel officiel d'inventaire en grille | Pour des rouleaux, kunais, pilules… |
| 🟢 | [Itemforge](https://github.com/theJ8910/Itemforge) | Système d'objets et d'inventaire | |
| 🟢 | [NauticalCoding/Inventory](https://github.com/NauticalCoding/Inventory) · [Millem1337/inventory](https://github.com/Millem1337/inventory) | Inventaires simples | |
| 🟢 | [Helix – personnages](https://github.com/NebulousCloud/helix/blob/master/gamemode/core/libs/sh_character.lua) | Système de personnages multiples | |
| 🟢 | [helix-plugins (Runian)](https://github.com/Runian/helix-plugins) | Plugins Helix, dont création de personnage simplifiée | |
| 🟢 | [helix-crafting](https://github.com/ZeMysticalTaco/helix-crafting) | Artisanat pour Helix | |
