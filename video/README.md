# 🎬 Vidéos musicales animées (format TikTok)

Génère une vidéo verticale **1080×1920** animée **au rythme d'une musique** :

- 🎵 **analyse de la musique** : tempo, beats, basses, spectre
- 🌀 **visualiseur circulaire** qui réagit aux fréquences, avec halo lumineux
- ✨ **particules** qui accélèrent avec les basses
- 🎤 **paroles mot par mot** : chaque mot « pop » à son temps, le mot chanté passe en couleur
- 💥 **effets sur les gros beats** : flash, zoom « punch », tremblement
- 🖼️ **tes images** (optionnel) qui changent tous les N beats, avec zoom et glissement

Tout se règle dans un seul fichier : **`script.json`**.

## 🚀 Utilisation

```bash
cd video
pip install -r requirements.txt          # + ffmpeg installé sur la machine

# 1. Mets ta musique dans video/musique/ (mp3, wav, m4a…)
# 2. Modifie script.json (nom de la musique, paroles, couleurs…)
# 3. Repère les beats pour caler tes paroles :
python generer_video.py script.json --beats

# 4. Aperçu rapide (demi-résolution) :
python generer_video.py script.json --apercu

# 5. Vidéo finale :
python generer_video.py script.json
```

La vidéo est créée dans `video/sortie/` (ex. `sortie/script.mp4`).

Pas encore de musique ? `python demo_beat.py` crée `musique/demo.wav` (un beat à 120 BPM généré par code, libre de droits) — c'est celle qu'utilise l'exemple.

## ✍️ Le script (`script.json`)

| Clé | Rôle |
|---|---|
| `musique` | fichier audio, chemin relatif au script (ex. `musique/mon_son.mp3`) |
| `debut`, `duree` | extrait à utiliser, en secondes (ex. le refrain : `"debut": 42.5, "duree": 15`) |
| `bpm` | optionnel — force le tempo si la détection auto se trompe |
| `titre`, `sous_titre` | texte fixe en haut (laisser `""` pour masquer) |
| `couleurs` | `fond_haut`, `fond_bas`, `accent` (mot chanté, barres), `accent2`, `texte` |
| `visualiseur`, `particules`, `flash` | `true` / `false` pour activer chaque effet |
| `images` | liste d'images, ex. `["images/1.jpg", "images/2.jpg"]` — vide = fond dégradé |
| `images_tous_les_n_beats` | rythme de changement d'image |
| `taille_paroles` | taille du texte des paroles |
| `police` | optionnel — chemin vers un fichier `.ttf` / `.otf` |
| `paroles` | liste de lignes (voir ci-dessous) |

**Paroles** — les temps sont en secondes **depuis `debut`** :

```json
{ "debut": 4.0, "fin": 7.9, "texte": "Chaque mot apparaît en rythme" }
```

Les mots sont répartis automatiquement sur la ligne. Pour caler chaque mot précisément, ajoute `mots` (un temps par mot) :

```json
{ "debut": 12.0, "fin": 15.9, "texte": "Tu peux caler chaque mot", "mots": [12.0, 12.5, 13.0, 14.0, 15.0] }
```

Astuce : `--beats` affiche les temps de tous les beats (`●` = beat fort) — pose tes mots dessus pour un rendu bien synchro.

## 🎨 Thèmes sur mesure

`"theme": "capuche"` remplace le visuel par défaut par un univers **rue de nuit** (fichier `theme_capuche.py`) : silhouette à capuche aux yeux rouges, lune rouge sang entourée d'un spectre, skyline dont les immeubles montent et descendent comme un égaliseur, pluie, grain de film.

- **Impacts** : un mot s'écrase à l'écran (onde de choc, flash, tremblement, glitch).
- **Pause** avant le drop : la pluie ralentit, zoom sur la capuche, le mot du drop s'écrit lettre par lettre.
- **Scènes** qui illustrent les paroles, chacune sur une plage de temps (`theme_capuche.py` + `scenes_capuche.py`) :

| Effet | Ce qui se passe |
|---|---|
| `vent` | rafales, pluie couchée, brouillard qui file |
| `ame_noire` | fumée noire qui s'échappe de la capuche, la lune s'assombrit |
| `pare_brise` | gouttes qui coulent sur l'écran, larmes rouges sous les yeux |
| `yeux_rouges` | zoom sur les yeux qui brûlent, phares qui filent sur la route |
| `matrice` | pluie de code rouge derrière la silhouette |
| `sourire` | sourire lumineux dans l'ombre de la capuche, une larme |
| `cicatrices` | griffures qui lacèrent l'écran (sur les temps donnés dans `temps`) |
| `peace` | la pluie s'arrête, la lune s'éclaircit, tout se calme |
| `horloge` | la lune devient une horloge dont les aiguilles s'emballent |
| `tempete` | éclairs sur les gros beats, ciel qui flashe, pluie battante |
| `palmiers` | coucher de soleil de Los Angeles, palmiers qui surgissent |
| `flammes` | la ville brûle, les flammes suivent le spectre |
| `fumee_blanche` | braise et fumée blanche devant la capuche |
| `tresor` | pièces d'or qui tombent et scintillent |
| `regards` | des yeux rouges s'ouvrent dans l'ombre |
| `likes` | cœurs qui montent comme sur TikTok |
| `projecteur` | tout s'éteint sauf un faisceau sur la silhouette |
| `combat` | onde de choc à chaque temps, caméra qui cogne |
| `diamants` | diamants qui tombent en tournant |
| `nuit` | étoiles, étoile filante, lune en croissant |
| `souvenirs` | vieux film sépia qui scintille, rayures |
| `demons` | des cornes poussent sur la capuche |
| `aube` | soleil doré avec rayons, la pluie se calme |
| `gris` | tout passe en noir et blanc |
| `silhouettes` | d'autres capuches apparaissent autour (les frères, les cliquos) |
| `matin` | ciel bleu du matin, la silhouette disparaît presque |
| `lumiere` | rayons de lumière venus d'en haut |
| `ondes` | ondes sonores qui partent de la lune |
| `billets` | billets de 20 qui volent |
| `lettres_z` | des Z qui flottent |
| `glitch` | l'image se déchire et se décale |
| `gyrophares` | lumières de police rouge / bleu |
| `lune_tir` | viseur sur la lune, tir, la lune se fissure (`tir` = moment du tir) |
| `phases` | une ombre passe sur la lune (pleine → vide) |

Un impact peut être `"fort": false` : le mot s'écrase sans flash ni tremblement (pratique pour un mot clé par phrase).

**Exemples :**
- **`bang_x_capuche_complet.json`** — **le son entier (4:47)** : 46 phrases, chacune avec sa scène et son mot clé, BANG sur l'arrivée des basses, outro sous les étoiles.
- `bang_x_capuche.json` — extrait de 38 s (0:27 → 1:05) pour TikTok.

```bash
python generer_video.py bang_x_capuche_complet.json                       # 1080×1920 (~25 min)
python generer_video.py bang_x_capuche_complet.json --echelle 0.6667      # 720×1280, plus rapide et plus léger
```

## 🎵 Le son « Bang x Capuche » et ses extraits

Tout est dans `musique/` pour les prochains tests :

| Fichier | Contenu |
|---|---|
| `bang_x_capuche_remix.mp3` | le son complet (4:47, 117 BPM) |
| `bang_x_capuche_paroles.txt` | les paroles complètes |
| `bang_x_capuche_paroles_calees.json` | chaque ligne et chaque mot avec son temps dans le son (calage automatique, lignes douteuses corrigées à la main) |
| `bang_x_capuche_transcription.json` | transcription automatique brute, mot par mot (sert au calage) |
| `extraits/01_couplet1_debut_0m27-1m05.mp3` | début du couplet 1 (celui de la vidéo) |
| `extraits/02_couplet1_suite_1m05-1m52.mp3` | suite du couplet 1 (« Et le temps m'baise… ») |
| `extraits/03_refrain_1m52-2m25.mp3` | refrain (« Jamais lâché, peu d'quantité… ») |
| `extraits/04_couplet2_2m25-3m26.mp3` | couplet 2 (« Faut que j'apprenne à kiffer ma vie… ») |
| `extraits/05_fin_refrain_3m26-4m00.mp3` | fin du couplet 2 + dernier refrain |

Pour faire une vidéo sur un autre passage, récupère les paroles déjà calées avec les temps relatifs au début choisi, puis colle le résultat dans `"paroles"` du script :

```bash
python caler_paroles.py musique/bang_x_capuche_paroles.txt musique/bang_x_capuche_transcription.json \
    --debut 112 --fin 145 > paroles_refrain.json
```

Le pourcentage affiché pour chaque ligne indique la part des mots reconnus avec certitude. En dessous d'environ 50 %, vérifie le timing de la ligne dans un aperçu (`--apercu`), car la transcription du rap n'est pas parfaite.

## ⚠️ À savoir

- **Droits** : une musique protégée peut être utilisée sur TikTok si tu ajoutes le son **depuis la bibliothèque TikTok** ; pour publier ailleurs, utilise une musique dont tu as les droits.
- Les **emojis** ne s'affichent pas dans les paroles (la police ne les contient pas) — ajoute-les dans la description TikTok.
- Rendu : ~1 min pour 20 s en 1080p sur 4 cœurs (`--apercu` est ~4× plus rapide).
