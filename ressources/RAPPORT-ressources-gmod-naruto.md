# 🍥 Rapport de recherche : ressources Naruto / anime pour un serveur Garry's Mod

> Brouillon à valider : rien n'est encore publié sur GitHub.
> Recherche faite le 30/09/2026. Les pages Steam Workshop n'ont pas pu être ouvertes directement (réseau bloqué). Les infos Workshop viennent donc des résultats de recherche : vérifie chaque page avant de t'en servir.

---

## ⚠️ À lire d'abord : la question des droits

Les animations et modèles de **Naruto to Boruto: Shinobi Striker** appartiennent à **Bandai Namco** et à **Masashi Kishimoto / Shueisha**. Ce que ça implique :

- **On ne peut pas publier sur GitHub des animations extraites (« rippées ») du jeu.** C'est de la redistribution de contenu protégé. GitHub supprime ce genre de dépôt sur plainte DMCA, et le compte peut être sanctionné.
- **Bandai Namco fait retirer des contenus de fans** : des mods ont déjà été retirés du Workshop Steam et des vidéos de mods ont reçu des avertissements pour droits d'auteur ([exemple de discussion](https://steamcommunity.com/app/1778820/discussions/0/4299322040765922583/)).
- **Les créateurs des packs Workshop interdisent en général le ré-upload et la décompilation.** Le [wOS Naruto Animation and Sound Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=2473998307), par exemple, est libre d'utilisation mais interdit à la republication.

👉 **La bonne méthode pour un serveur GMod** : on ne copie pas les fichiers. On **référence** les addons Workshop dans une *collection* que les joueurs téléchargent eux-mêmes (c'est comme ça que tous les serveurs Naruto RP fonctionnent). Et on met sur GitHub **notre propre code** et des **ressources sous licence libre**.

---

## 1. 🎬 Animations prêtes pour GMod (Steam Workshop, à référencer, pas à copier)

| Ressource | Ce que c'est | Remarque |
|---|---|---|
| [[wOS] DynaBase – Dynamic Animation Manager](https://steamcommunity.com/sharedfiles/filedetails/?id=2916561591) | **Le socle moderne des animations** : on active, ordonne et ajoute des animations sans redémarrer. Un dev peut ajouter ses animations en Lua avec `IncludeModel()`. | Base recommandée pour un nouveau serveur |
| [Supported DynaBase Addons](https://steamcommunity.com/sharedfiles/filedetails/?id=2917006548) | Collection officielle des packs compatibles DynaBase | Point de départ pour choisir des packs |
| [[wOS] Animation Extension – Base (Full)](https://steamcommunity.com/workshop/filedetails/?id=757604550) / [(Code Only)](https://steamcommunity.com/sharedfiles/filedetails/?id=2646756503) | Ancienne base wOS, requise par beaucoup de packs plus anciens | Nécessaire pour le pack Naruto ci-dessous |
| [[wOS] Naruto Animation and Sound Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=2473998307) | **Animations style Naruto + sons de l'anime** | Libre d'utilisation, ré-upload interdit |
| [[wOS] The Ultimate Animation Pack](https://steamcommunity.com/sharedfiles/filedetails/?id=3539161114) | Gros pack d'animations wOS | À vérifier |
| [[wOS DynaBase] Mixamo Movement Animations](https://steamcommunity.com/workshop/filedetails/?id=2919093249) | Déplacements issus de Mixamo | Mouvements plus fluides |
| [Extended Player Animations [xdR/DynaBase]](https://steamcommunity.com/sharedfiles/filedetails/?id=2922279661) | Animations de joueur supplémentaires | |
| [[xdR-wOS] Sprinting Animation (DynaBase)](https://steamcommunity.com/sharedfiles/filedetails/?id=3276449370) | Animation de sprint | Utile pour la « course ninja » |
| [[wOS] Garry's Mod 9 Re-animations](https://steamcommunity.com/sharedfiles/filedetails/?id=2916764640) | Ré-animations GMod | |
| [Naruto: Ultimate Ninja Mega Pack for GMod](https://steamcommunity.com/workshop/filedetails/?id=3446243032) | Méga-pack Naruto | Contenu et origine à vérifier sur la page |

## 2. 🥷 Collections de serveurs Naruto RP existants (pour s'inspirer)

Ces collections montrent quels addons les serveurs Naruto RP utilisent réellement : modèles, jutsus, animations, cartes. Ne copie rien : regarde surtout les listes d'addons.

- 🇫🇷 [SL V5 – Les Shinobi en Action](https://steamcommunity.com/sharedfiles/filedetails/?id=2907980776) · [[FR-QC] YTG Naruto RP](https://steamcommunity.com/sharedfiles/filedetails/?id=2513266019) · [Naruto RP le monde ninja](https://steamcommunity.com/sharedfiles/filedetails/?id=2119260001) · [[FR] Naruto Rôleplay](https://steamcommunity.com/sharedfiles/filedetails/?id=1077921002)
- 🌍 [LDS Naruto RP](https://steamcommunity.com/workshop/filedetails/?id=3291374346) · [NARUTO RP](https://steamcommunity.com/sharedfiles/filedetails/?id=3343409051) · [VOIN Naruto RP](https://steamcommunity.com/workshop/filedetails/?id=2969093066) · [[NPS] Naruto RP](https://steamcommunity.com/sharedfiles/filedetails/?id=3414285999) · [[LNA] Naruto RP](https://steamcommunity.com/sharedfiles/filedetails/?id=2911367074) · [ATG NARUTO RP](https://steamcommunity.com/sharedfiles/filedetails/?id=3611309126) · [NARUTO WORLD RP](https://steamcommunity.com/sharedfiles/filedetails/?id=1140486740)

> Si on lit ces listes en détail, on pourra en tirer la liste des addons « incontournables » (modèles Shinobi Striker, jutsus, cartes de Konoha…) pour **ta** collection. On pourra le faire une fois l'accès à Steam débloqué, ou si tu m'envoies le contenu des pages.

## 3. 🧱 Bases de code open source (GitHub) pour le serveur

| Projet | Utilité |
|---|---|
| [NebulousCloud/helix](https://github.com/NebulousCloud/helix) | **Framework RP open source** (successeur de NutScript) : personnages, inventaires, factions… Idéal pour un Naruto RP « sérieux » |
| [DarkRP (FPtje)](https://github.com/FPtje/DarkRP) | Le gamemode RP le plus répandu. Beaucoup de serveurs Naruto RP partent de là |
| [Aykiiro/Aykii_HUD](https://github.com/Aykiiro/Aykii_HUD) | Exemple de HUD Naruto RP pour DarkRP |
| [Facepunch/garrysmod](https://github.com/Facepunch/garrysmod) | Le code Lua officiel de GMod (dont `animations.lua` : comment le jeu choisit les animations du joueur) |
| [robotboy655/gmod-animations](https://github.com/robotboy655/gmod-animations) | Sources **SMD/QC** des animations de joueur de GMod : le modèle à suivre pour compiler ses propres packs d'animations (licence à vérifier) |
| [JetBoom/animationsapi](https://github.com/JetBoom/animationsapi) | API pour des animations stockées en tables Lua (sans compiler de modèle) |
| [buu342/GMod-BlenderLuaAnimationsAPIExport](https://github.com/buu342/GMod-BlenderLuaAnimationsAPIExport) | Exporte des animations Blender vers cette API Lua |
| [vlazed/smh2blender](https://github.com/vlazed/smh2blender) | Échange d'animations entre Blender et Stop Motion Helper (GMod) |
| [TomDotBat/gmod-templates](https://github.com/TomDotBat/gmod-templates) | Modèles de code (SWEP, entités…) : base pour coder des **jutsus en SWEP** |
| [Be1zebub/Small-GLua-Things](https://github.com/Be1zebub/Small-GLua-Things) | Bibliothèques, snippets et exemples GLua |
| [Wiki officiel GMod](https://wiki.facepunch.com/gmod) | Documentation complète de l'API Lua |

## 4. 🛠️ Outils pour créer ses propres animations et modèles

| Outil | Rôle |
|---|---|
| [Blender](https://www.blender.org) + [Blender Source Tools](http://steamreview.org/BlenderSourceTools/) ([GitHub](https://github.com/Artfunkel/BlenderSourceTools)) | Import/export SMD, DMX et QC (format Source). Nécessite Blender 4.1+ |
| [Crowbar](https://github.com/ZeqMacaw/Crowbar) | Compiler et décompiler des modèles Source, publier sur le Workshop |
| [DarklightGames/io_scene_psk_psa](https://github.com/DarklightGames/io_scene_psk_psa) | Import/export des formats Unreal PSK/PSA dans Blender |
| [FModel](https://github.com/4sval/FModel) / [UE Viewer](https://github.com/gildor2/UEViewer) | Explorateurs de fichiers de jeux Unreal Engine |
| [VRoid Studio](https://vroid.com/en/studio) + [VRM Add-on for Blender](https://github.com/saturday06/VRM-Addon-for-Blender) | **Créer tes propres personnages style anime** ; [guide de portage vers GMod](https://steamcommunity.com/sharedfiles/filedetails/?id=3079067248) |

> ℹ️ Il existe des guides pour extraire les fichiers de Shinobi Striker (le jeu tourne sous Unreal Engine). Techniquement c'est faisable pour un usage **perso**, mais le résultat ne peut pas être republié. Je ne mets donc pas la procédure détaillée dans ce dépôt.

## 5. ✅ Ressources vraiment libres (qu'on PEUT mettre sur GitHub)

| Ressource | Licence | Intérêt |
|---|---|---|
| [Quaternius – Universal Animation Library](https://quaternius.itch.io/universal-animation-library) et [UAL 2](https://quaternius.itch.io/universal-animation-library-2) | **CC0** (domaine public) | 250+ animations : **combos de combat à 3-4 coups**, esquives, déplacements. Fichiers .blend, compatibles squelette Mixamo. Base idéale pour des animations de jutsu/taijutsu **à toi** |
| [Quaternius – autres packs](https://quaternius.com/) | CC0 | Personnages, décors |
| [Mixamo](https://www.mixamo.com) | Gratuit, **utilisable dans un jeu mais pas redistribuable en fichiers bruts** | Énorme bibliothèque d'arts martiaux. OK dans un addon compilé, pas en vrac sur GitHub |
| [Sonniss GDC Game Audio Bundle](https://gdc.sonniss.com/) ([archives](https://sonniss.com/gameaudiogdc/)) | Libre de droits, usage commercial, sans attribution | Des centaines de Go de bruitages (impacts, whoosh, explosions) pour les jutsus. Interdit pour l'entraînement d'IA |
| [Freesound](https://freesound.org) | Variable (filtrer sur CC0) | Sons ponctuels |

---

## 💡 Ma proposition pour le dépôt de ressources

Créer un **dépôt séparé**, par exemple `gmod-ressources`, qui contiendrait :

```
gmod-ressources/
├── README.md                  ← index de tout ce rapport (liens + licences)
├── workshop/
│   └── collection-naruto.md   ← liste des addons Workshop à abonner (liens, pas de fichiers)
├── lua/
│   ├── jutsu_base/            ← NOTRE base de SWEP « jutsu » (chakra, cooldown, animation, effet)
│   └── dynabase_register/     ← exemple d'enregistrement de nos animations dans DynaBase
├── animations/
│   └── sources/               ← nos animations créées à partir des packs CC0 (Quaternius)
├── sons/                      ← bruitages CC0 / Sonniss uniquement
├── guides/
│   ├── blender-vers-gmod.md   ← pipeline Blender → SMD → Crowbar → GMod
│   └── vroid-vers-gmod.md     ← créer un perso anime original
└── LICENCES.md                ← origine et licence de chaque fichier
```

**Ce que je ne mettrai pas dedans :** les fichiers extraits de Shinobi Striker ou d'autres jeux, et les addons Workshop recopiés.

### Prochaines étapes possibles
1. Tu valides (ou modifies) ce plan.
2. Je crée le dépôt et j'écris la base de code « jutsu » (SWEP + chakra + cooldowns + animations DynaBase), les guides et l'index.
3. On prépare ta collection Workshop Naruto RP à partir des serveurs existants.
