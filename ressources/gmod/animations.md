# 🎬 Garry's Mod – Animations

[← Sommaire](../README.md) · Légende : 🟢 libre · 🟡 conditions · 🔵 outil/doc · 🔴 référence seulement

## Comment ça marche dans GMod

Les animations des joueurs sont des **séquences** compilées dans des modèles (`.mdl`). Pour ajouter des animations sans modifier le jeu, on utilise une **base d'animation** (wOS / DynaBase) qui charge des packs d'animations. Sur un serveur, les joueurs téléchargent ces packs via la **collection Workshop** du serveur.

## 🧱 Bases d'animation

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔴 | [[wOS] DynaBase – Dynamic Animation Manager](https://steamcommunity.com/sharedfiles/filedetails/?id=2916561591) | **Base moderne** : active, ordonne et ajoute des animations en direct. En Lua, `IncludeModel()` ajoute tes propres animations | Recommandée pour un nouveau serveur |
| 🔴 | [Supported DynaBase Addons](https://steamcommunity.com/sharedfiles/filedetails/?id=2917006548) | Collection des packs compatibles DynaBase | |
| 🔴 | [[wOS] Animation Extension – Base (Full)](https://steamcommunity.com/workshop/filedetails/?id=757604550) · [(Code Only)](https://steamcommunity.com/sharedfiles/filedetails/?id=2646756503) | Ancienne base wOS | Requise par les packs plus anciens |
| 🔴 | [xdReanimsBase](https://steamcommunity.com/sharedfiles/filedetails/?id=2143558752) | Autre base d'animations | |

## 📦 Packs d'animations (Workshop)

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🔴 | [[wOS] The Ultimate Animation Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3539161114) | Gros pack wOS | |
| 🔴 | [[wOS DynaBase] Mixamo Movement Animations](https://steamcommunity.com/workshop/filedetails/?id=2919093249) | Déplacements plus naturels | |
| 🔴 | [Extended Player Animations [xdR/DynaBase]](https://steamcommunity.com/sharedfiles/filedetails/?id=2922279661) | Animations de joueur supplémentaires | |
| 🔴 | [[xdR-wOS] Sprinting Animation (DynaBase)](https://steamcommunity.com/sharedfiles/filedetails/?id=3276449370) | Sprint | |
| 🔴 | [[wOS] Garry's Mod 9 Re-animations](https://steamcommunity.com/sharedfiles/filedetails/?id=2916764640) | Ré-animations | |
| 🔴 | [[wOS] Animation Extension – Prone Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=918084741) | Se coucher / ramper | |

➡️ Packs spécifiques à Naruto : voir [projets/naruto-rp](../projets/naruto-rp/README.md).

## 🛠️ Créer ses propres animations

**Chaîne de travail classique :** animation dans **Blender** → export **SMD** (Blender Source Tools) → fichier **QC** listant les `$sequence` → compilation avec **Crowbar** → chargement via DynaBase (`IncludeModel`).

| | Ressource | Contenu | Remarque |
|---|---|---|---|
| 🟢 | [robotboy655/gmod-animations](https://github.com/robotboy655/gmod-animations) | Les **sources SMD/QC** des animations de joueur de GMod | Le modèle parfait pour structurer tes QC. Licence non précisée : s'en inspirer, ne pas recopier |
| 🔵 | [Blender Source Tools](http://steamreview.org/BlenderSourceTools/) ([GitHub](https://github.com/Artfunkel/BlenderSourceTools)) | Import/export SMD, DMX, QC dans Blender | Blender 4.1+ |
| 🔵 | [Crowbar](https://github.com/ZeqMacaw/Crowbar) | Compiler/décompiler les modèles | |
| 🟢 | [smh2blender](https://github.com/vlazed/smh2blender) | Échanger des animations entre Blender et Stop Motion Helper | Pratique pour animer directement dans GMod |
| 🟢 | [animationsapi](https://github.com/JetBoom/animationsapi) + [exporteur Blender](https://github.com/buu342/GMod-BlenderLuaAnimationsAPIExport) | Animations en Lua, sans compilation | |
| 🟢 | [Quaternius – Universal Animation Library](https://quaternius.itch.io/universal-animation-library) · [UAL 2](https://quaternius.itch.io/universal-animation-library-2) | **250+ animations CC0**, dont des combos de combat à 3-4 coups | **Meilleure base libre** pour créer nos animations |
| 🟡 | [Mixamo](https://www.mixamo.com) | Des milliers d'animations (arts martiaux…), rig automatique | OK dans un addon compilé, **fichiers bruts non redistribuables** |
| 🔵 | [DarklightGames/io_scene_psk_psa](https://github.com/DarklightGames/io_scene_psk_psa) | Importer des animations au format Unreal (PSA) dans Blender | Pour des sources Unreal **libres** |

> 💡 Le retargeting (transférer une animation d'un squelette à un autre, par ex. Mixamo → ValveBiped) se fait dans Blender avec des addons comme « Rokoko Studio Live » ou « Auto-Rig Pro ». Cherche « retarget mixamo to valvebiped » pour des tutoriels.
