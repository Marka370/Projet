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

`"theme": "capuche"` remplace le visuel par défaut par un univers **rue de nuit** (fichier `theme_capuche.py`) : silhouette à capuche aux yeux rouges, lune rouge sang entourée d'un spectre, skyline dont les immeubles montent et descendent comme un égaliseur, pluie, grain de film. Les **impacts** (« BANG »…) écrasent un mot à l'écran avec onde de choc, flash, tremblement et glitch. La **pause** avant le drop ralentit la pluie, zoome sur la capuche et écrit le mot du drop lettre par lettre.

Exemple complet : `bang_x_capuche.json` (passage 0:31 → 1:01 du son, impacts calés sur les gros coups de basse, tous les 16 temps).

```bash
python generer_video.py bang_x_capuche.json
```

## ⚠️ À savoir

- **Droits** : une musique protégée peut être utilisée sur TikTok si tu ajoutes le son **depuis la bibliothèque TikTok** ; pour publier ailleurs, utilise une musique dont tu as les droits.
- Les **emojis** ne s'affichent pas dans les paroles (la police ne les contient pas) — ajoute-les dans la description TikTok.
- Rendu : ~1 min pour 20 s en 1080p sur 4 cœurs (`--apercu` est ~4× plus rapide).
