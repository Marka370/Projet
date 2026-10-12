"""Génère une vidéo verticale (TikTok / Reels / Shorts) animée sur une musique.

Tout est piloté par un fichier « script » JSON (voir script.json) :
paroles synchronisées, images, couleurs, extrait de la musique à utiliser.

La musique est analysée (beats, basses, spectre) et chaque élément réagit :
  - fond dégradé ou images qui changent sur les beats (zoom + Ken Burns)
  - visualiseur circulaire avec halo lumineux
  - particules qui accélèrent avec les basses
  - paroles qui apparaissent mot par mot, le mot chanté en couleur
  - flash, tremblement et zoom « punch » sur les gros beats

Usage :
    python generer_video.py script.json
    python generer_video.py script.json --apercu        # rendu rapide basse qualité
    python generer_video.py script.json --beats         # affiche les temps des beats
"""

import argparse
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

DOSSIER = Path(__file__).resolve().parent

POLICES = [
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]

DEFAUTS = {
    "largeur": 1080,
    "hauteur": 1920,
    "fps": 30,
    "debut": 0.0,
    "duree": None,
    "bpm": None,
    "titre": "",
    "sous_titre": "",
    "couleurs": {
        "fond_haut": "#1a0b3d",
        "fond_bas": "#05010f",
        "accent": "#ff2d75",
        "accent2": "#29e7ff",
        "texte": "#ffffff",
    },
    "visualiseur": True,
    "particules": True,
    "flash": True,
    "images": [],
    "images_tous_les_n_beats": 4,
    "paroles": [],
    "taille_paroles": 92,
    "position_paroles": 0.66,
    "police": None,
    "theme": None,
}


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def melanger(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease_out_back(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.9, 2.9
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def charger_police(cfg, taille):
    for chemin in ([cfg["police"]] if cfg.get("police") else []) + POLICES:
        if chemin and os.path.exists(chemin):
            return ImageFont.truetype(chemin, taille)
    return ImageFont.load_default(taille)


def charger_script(chemin):
    with open(chemin, encoding="utf-8") as f:
        brut = json.load(f)
    cfg = {**DEFAUTS, **brut}
    cfg["couleurs"] = {**DEFAUTS["couleurs"], **brut.get("couleurs", {})}
    base = Path(chemin).resolve().parent
    cfg["musique"] = str((base / cfg["musique"]).resolve())
    cfg["images"] = [str((base / i).resolve()) for i in cfg["images"]]
    return cfg


# --------------------------------------------------------------------------- #
# Analyse audio
# --------------------------------------------------------------------------- #

def analyser_audio(cfg, n_bandes=48):
    import librosa

    y, sr = librosa.load(cfg["musique"], sr=22050, mono=True,
                         offset=cfg["debut"], duration=cfg["duree"])
    duree = len(y) / sr
    hop = 512

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048, hop_length=hop,
                                         n_mels=n_bandes, fmax=11000)
    db = librosa.power_to_db(mel, ref=np.max)
    bas, haut = np.percentile(db, 5, axis=1, keepdims=True), np.percentile(db, 99, axis=1, keepdims=True)
    spectre = np.clip((db - bas) / np.maximum(haut - bas, 1e-6), 0, 1)

    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    # Tempo : celui du script s'il est donné, sinon la médiane du tempo local
    # (plus fiable que l'estimation globale, qui tombe parfois sur 2/3 du vrai tempo)
    bpm = cfg.get("bpm") or float(np.median(librosa.feature.tempo(
        onset_envelope=onset, sr=sr, hop_length=hop, aggregate=None)))
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset, sr=sr, hop_length=hop, bpm=bpm)
    t_beats = librosa.frames_to_time(beats, sr=sr, hop_length=hop)

    basses = spectre[:6].mean(axis=0)
    t_spec = librosa.frames_to_time(np.arange(spectre.shape[1]), sr=sr, hop_length=hop)

    # Ré-échantillonnage aux images de la vidéo
    fps = cfg["fps"]
    n_images = int(duree * fps)
    t_img = np.arange(n_images) / fps
    spec_img = np.stack([np.interp(t_img, t_spec, b) for b in spectre])
    basses_img = np.interp(t_img, t_spec, basses)

    # Lissage attaque rapide / relâche lente (les barres retombent en douceur)
    def lisser(x, relache=0.82):
        out = np.empty_like(x)
        prev = x[..., 0]
        for i in range(x.shape[-1]):
            prev = np.maximum(x[..., i], prev * relache)
            out[..., i] = prev
        return out

    spec_img = lisser(spec_img)
    basses_img = lisser(basses_img, 0.86)
    basses_img = (basses_img - basses_img.min()) / max(np.ptp(basses_img), 1e-6)

    # Beats « forts » = ceux où les basses sont au-dessus de la médiane
    force = np.interp(t_beats, t_img, basses_img) if len(t_beats) else np.array([])
    seuil = np.median(force) if len(force) else 1
    forts = t_beats[force >= seuil]

    tempo = float(np.atleast_1d(tempo)[0])
    return {
        "duree": n_images / fps,
        "n_images": n_images,
        "spectre": spec_img.astype(np.float32),
        "basses": basses_img.astype(np.float32),
        "beats": t_beats,
        "beats_forts": forts,
        "tempo": tempo,
    }


def impulsion(t, temps, decroissance):
    """Valeur 1 → 0 qui décroît après le dernier événement (beat)."""
    i = np.searchsorted(temps, t, side="right") - 1
    if i < 0:
        return 0.0, -1
    return math.exp(-(t - temps[i]) / decroissance), i


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #

class Rendu:
    def __init__(self, cfg, audio, echelle=1.0):
        self.cfg, self.audio = cfg, audio
        self.W = int(cfg["largeur"] * echelle) // 2 * 2
        self.H = int(cfg["hauteur"] * echelle) // 2 * 2
        self.s = echelle
        c = cfg["couleurs"]
        self.c_haut, self.c_bas = hex_rgb(c["fond_haut"]), hex_rgb(c["fond_bas"])
        self.c_acc, self.c_acc2, self.c_txt = hex_rgb(c["accent"]), hex_rgb(c["accent2"]), hex_rgb(c["texte"])

        self.police_paroles = charger_police(cfg, int(cfg["taille_paroles"] * echelle))
        self.police_titre = charger_police(cfg, int(64 * echelle))
        self.police_sous = charger_police(cfg, int(38 * echelle))
        self.cache_mots = {}

        # Vignette (assombrit les bords)
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        d = np.sqrt(((xx - self.W / 2) / (self.W * 0.75)) ** 2 + ((yy - self.H / 2) / (self.H * 0.7)) ** 2)
        self.vignette = np.clip(1.15 - d * 0.75, 0.35, 1.0)[..., None]
        self.grad = np.linspace(0, 1, self.H, dtype=np.float32)[:, None, None]

        # Particules déterministes
        rng = np.random.default_rng(7)
        n = 90
        self.p_x = rng.random(n)
        self.p_y0 = rng.random(n)
        self.p_v = 0.03 + rng.random(n) * 0.06
        self.p_taille = 2 + rng.random(n) * 6
        self.p_phase = rng.random(n) * 6.28
        self.p_couleur = rng.random(n) < 0.5
        self.p_avance = np.cumsum(0.4 + audio["basses"] * 2.2) / cfg["fps"]

        self.images = [self._preparer_image(p) for p in cfg["images"]]
        self.paroles = self._preparer_paroles(cfg["paroles"])

        # Thème visuel sur mesure (ex. « capuche ») : remplace le rendu par défaut
        self.theme = None
        if cfg.get("theme") == "capuche":
            from theme_capuche import ThemeCapuche
            self.theme = ThemeCapuche(self)

    # ---- préparation -------------------------------------------------------

    def _preparer_image(self, chemin):
        img = Image.open(chemin).convert("RGB")
        # Recadrage « cover » avec 15 % de marge pour le zoom / Ken Burns
        cible_w, cible_h = int(self.W * 1.15), int(self.H * 1.15)
        r = max(cible_w / img.width, cible_h / img.height)
        img = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
        g = (img.width - cible_w) // 2, (img.height - cible_h) // 2
        return img.crop((g[0], g[1], g[0] + cible_w, g[1] + cible_h))

    def _preparer_paroles(self, paroles):
        lignes = []
        largeur_max = self.W * 0.86
        draw = ImageDraw.Draw(Image.new("L", (1, 1)))
        espace = draw.textlength(" ", font=self.police_paroles) * 1.6
        hauteur_ligne = self.police_paroles.size * 1.18
        for p in paroles:
            mots = p["texte"].split()
            debut, fin = float(p["debut"]), float(p["fin"])
            # Temps de chaque mot : fournis, sinon répartis sur 70 % de la ligne
            if "mots" in p:
                temps = [float(x) for x in p["mots"]]
            else:
                pas = (fin - debut) * 0.7 / max(len(mots), 1)
                temps = [debut + i * pas for i in range(len(mots))]
            # Retour à la ligne automatique
            rangees, courante, larg = [], [], 0
            for i, m in enumerate(mots):
                lm = draw.textlength(m, font=self.police_paroles)
                if courante and larg + espace + lm > largeur_max:
                    rangees.append((courante, larg))
                    courante, larg = [], 0
                larg += (espace if courante else 0) + lm
                courante.append((i, m, lm))
            if courante:
                rangees.append((courante, larg))
            places = []
            y0 = self.H * self.cfg["position_paroles"] - (len(rangees) - 1) * hauteur_ligne / 2
            for r, (rangee, larg) in enumerate(rangees):
                x = (self.W - larg) / 2
                for i, m, lm in rangee:
                    places.append({"mot": m, "t": temps[i], "cx": x + lm / 2, "cy": y0 + r * hauteur_ligne})
                    x += lm + espace
            for k, pl in enumerate(places):
                pl["t_suiv"] = places[k + 1]["t"] if k + 1 < len(places) else fin
            lignes.append({"debut": debut, "fin": fin, "mots": places})
        return lignes

    def _image_mot(self, mot, couleur):
        cle = (mot, couleur)
        if cle not in self.cache_mots:
            f = self.police_paroles
            contour = max(2, int(f.size * 0.07))
            l, t, r, b = f.getbbox(mot, stroke_width=contour)
            img = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            d.text((4 - l, 4 - t), mot, font=f, fill=couleur + (255,),
                   stroke_width=contour, stroke_fill=(0, 0, 0, 255))
            ombre = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ombre.putalpha(img.getchannel("A").filter(ImageFilter.GaussianBlur(f.size * 0.12)))
            self.cache_mots[cle] = (img, ombre)
        return self.cache_mots[cle]

    # ---- couches -----------------------------------------------------------

    def fond(self, i, t, pulse):
        if self.images:
            n = self.cfg["images_tous_les_n_beats"]
            beats = self.audio["beats"]
            nb = int(np.searchsorted(beats, t, side="right"))
            idx = (nb // n) % len(self.images)
            debut_img = beats[(nb // n) * n - 1] if (nb // n) * n - 1 >= 0 and len(beats) else 0.0
            age = t - debut_img
            img = self.images[idx]
            # Ken Burns : lent dézoom + glissement, alterné selon l'image
            z = 1.06 + 0.12 * math.exp(-age * 3.0) + 0.03 * pulse
            cw, ch = img.width / z, img.height / z
            sens = 1 if idx % 2 else -1
            cx = img.width / 2 + sens * min(age / 6, 1) * (img.width - cw) / 2 * 0.9
            cy = img.height / 2
            boite = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
            im = img.resize((self.W, self.H), Image.BILINEAR, box=boite)
            arr = np.asarray(im, dtype=np.float32) * (0.55 + 0.12 * pulse)
            teinte = np.array(melanger(self.c_haut, self.c_bas, 0.5), dtype=np.float32)
            return arr * 0.8 + teinte * 0.2
        haut = np.array(self.c_haut, np.float32)
        bas = np.array(self.c_bas, np.float32)
        # Le dégradé « respire » avec les basses
        haut = haut * (1 + 0.6 * self.audio["basses"][i]) + np.array(self.c_acc, np.float32) * 0.12 * pulse
        g = self.grad ** (1.2 + 0.4 * math.sin(t * 0.5))
        col = haut * (1 - g) + bas * g
        return np.broadcast_to(col, (self.H, self.W, 3)).copy()

    def particules(self, calque, i, t):
        d = ImageDraw.Draw(calque)
        av = self.p_avance[i]
        y = (self.p_y0 - av * self.p_v) % 1.0
        x = self.p_x + 0.02 * np.sin(t * 1.3 + self.p_phase)
        for k in range(len(self.p_x)):
            r = self.p_taille[k] * self.s * (1 + 0.6 * self.audio["basses"][i])
            px, py = x[k] * self.W, y[k] * self.H
            c = self.c_acc if self.p_couleur[k] else self.c_acc2
            a = int(120 + 100 * math.sin(t * 2 + self.p_phase[k]) ** 2)
            d.ellipse((px - r, py - r, px + r, py + r), fill=c + (a,))

    def visualiseur(self, calque, i, t, pulse):
        d = ImageDraw.Draw(calque)
        spec = self.audio["spectre"][:, i]
        n = len(spec)
        cx, cy = self.W / 2, self.H * 0.36
        r0 = self.W * (0.2 + 0.035 * self.audio["basses"][i] + 0.02 * pulse)
        long_max = self.W * 0.2
        epaisseur = max(3, int(self.W * 0.011))
        rot = t * 0.25
        # Barres en miroir (gauche / droite) pour un rendu symétrique
        for k in range(2 * n):
            v = spec[k if k < n else 2 * n - 1 - k]
            ang = rot + k / (2 * n) * 2 * math.pi
            l = 6 * self.s + v ** 1.4 * long_max
            ca, sa = math.cos(ang), math.sin(ang)
            c = melanger(self.c_acc2, self.c_acc, v)
            d.line((cx + ca * r0, cy + sa * r0, cx + ca * (r0 + l), cy + sa * (r0 + l)),
                   fill=c + (255,), width=epaisseur)
        # Anneau central
        e = max(4, int(8 * self.s))
        d.ellipse((cx - r0 + e * 2, cy - r0 + e * 2, cx + r0 - e * 2, cy + r0 - e * 2),
                  outline=self.c_txt + (230,), width=e)
        r1 = r0 * 0.55 * (1 + 0.25 * pulse)
        d.ellipse((cx - r1, cy - r1, cx + r1, cy + r1), fill=self.c_acc + (int(90 + 120 * pulse),))

    def textes(self, img, t, pulse):
        self.textes_fixes(img)
        self.textes_paroles(img, t, pulse)

    def textes_fixes(self, img):
        d = ImageDraw.Draw(img)
        cfg = self.cfg
        if cfg["titre"]:
            y = self.H * 0.09
            d.text((self.W / 2, y), cfg["titre"].upper(), font=self.police_titre, anchor="mm",
                   fill=self.c_txt, stroke_width=max(2, int(4 * self.s)), stroke_fill=(0, 0, 0))
        if cfg["sous_titre"]:
            d.text((self.W / 2, self.H * 0.09 + 70 * self.s), cfg["sous_titre"], font=self.police_sous,
                   anchor="mm", fill=self.c_acc2, stroke_width=max(1, int(3 * self.s)), stroke_fill=(0, 0, 0))

    def textes_paroles(self, img, t, pulse):
        for ligne in self.paroles:
            if not (ligne["debut"] - 0.05 <= t <= ligne["fin"] + 0.25):
                continue
            sortie = max(0.0, (t - ligne["fin"]) / 0.25)
            for m in ligne["mots"]:
                age = t - m["t"]
                if age < 0:
                    continue
                actif = m["t"] <= t < m["t_suiv"]
                couleur = self.c_acc if actif else self.c_txt
                mot, ombre = self._image_mot(m["mot"], couleur)
                ech = (0.35 + 0.65 * ease_out_back(age / 0.22)) * (1 + 0.05 * pulse * actif)
                ech *= 1 - 0.3 * sortie
                w, h = max(1, int(mot.width * ech)), max(1, int(mot.height * ech))
                m_img = mot.resize((w, h), Image.BILINEAR)
                o_img = ombre.resize((w, h), Image.BILINEAR)
                alpha = 1 - sortie
                if alpha < 1:
                    m_img.putalpha(m_img.getchannel("A").point(lambda a: int(a * alpha)))
                    o_img.putalpha(o_img.getchannel("A").point(lambda a: int(a * alpha)))
                dy = -sortie * 40 * self.s
                pos = (int(m["cx"] - w / 2), int(m["cy"] - h / 2 + dy))
                img.alpha_composite(o_img, (pos[0] + int(6 * self.s), pos[1] + int(8 * self.s)))
                img.alpha_composite(m_img, pos)

    # ---- assemblage --------------------------------------------------------

    def image(self, i):
        if self.theme:
            return self.theme.image(i)
        fps = self.cfg["fps"]
        t = i / fps
        pulse, _ = impulsion(t, self.audio["beats"], 0.14)
        fort, n_fort = impulsion(t, self.audio["beats_forts"], 0.10)

        scene = Image.fromarray(np.clip(self.fond(i, t, pulse), 0, 255).astype(np.uint8)).convert("RGBA")

        calque = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        if self.cfg["particules"]:
            self.particules(calque, i, t)
        if self.cfg["visualiseur"]:
            self.visualiseur(calque, i, t, pulse)
        # Halo lumineux : flou du calque calculé en basse résolution
        petit = calque.resize((self.W // 4, self.H // 4), Image.BILINEAR)
        halo = petit.filter(ImageFilter.GaussianBlur(6)).resize((self.W, self.H), Image.BILINEAR)
        scene.alpha_composite(halo)
        scene.alpha_composite(halo)
        scene.alpha_composite(calque)

        # Zoom « punch » + tremblement sur les beats forts
        if self.cfg["flash"] and fort > 0.02:
            z = 1 + 0.05 * fort
            rng = np.random.default_rng(n_fort)
            ox, oy = rng.uniform(-1, 1, 2) * 18 * self.s * fort
            cw, ch = self.W / z, self.H / z
            boite = ((self.W - cw) / 2 + ox, (self.H - ch) / 2 + oy, (self.W + cw) / 2 + ox, (self.H + ch) / 2 + oy)
            scene = scene.resize((self.W, self.H), Image.BILINEAR, box=boite)

        # Vignette avant les textes pour qu'ils restent bien lisibles
        arr = np.asarray(scene.convert("RGB"), dtype=np.float32) * self.vignette
        scene = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        self.textes(scene, t, pulse)

        arr = np.asarray(scene.convert("RGB"), dtype=np.float32)
        if self.cfg["flash"] and fort > 0.02:
            arr = arr + (255 - arr) * (0.35 * fort ** 2)

        # Barre de progression
        h = max(4, int(8 * self.s))
        x = int(self.W * (t / self.audio["duree"]))
        arr[self.H - h:, :x] = self.c_acc
        return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


# --------------------------------------------------------------------------- #
# Multiprocessing + ffmpeg
# --------------------------------------------------------------------------- #

_RENDU = None


def _init(cfg, audio, echelle):
    global _RENDU
    _RENDU = Rendu(cfg, audio, echelle)


def _image(i):
    return _RENDU.image(i)


def generer(cfg, sortie, echelle=1.0, crf=18):
    print(f"Analyse de {Path(cfg['musique']).name}…")
    audio = analyser_audio(cfg)
    print(f"  {audio['duree']:.1f} s · {audio['tempo']:.0f} BPM · {len(audio['beats'])} beats")
    r = Rendu(cfg, {**audio}, echelle)  # vérifie la config (images, polices) avant de lancer
    W, H, fps = r.W, r.H, cfg["fps"]

    sortie.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
        "-ss", str(cfg["debut"]), "-t", str(audio["duree"]), "-i", cfg["musique"],
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
        str(sortie),
    ]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = audio["n_images"]
    with Pool(os.cpu_count(), initializer=_init, initargs=(cfg, audio, echelle)) as pool:
        for k, data in enumerate(pool.imap(_image, range(n), chunksize=4)):
            ff.stdin.write(data)
            if k % fps == 0 or k == n - 1:
                print(f"\r  rendu {k + 1}/{n} images ({100 * (k + 1) // n} %)", end="", flush=True)
    ff.stdin.close()
    ff.wait()
    print()
    if ff.returncode:
        sys.exit("ffmpeg a échoué")
    print(f"✅ Vidéo créée : {sortie}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", nargs="?", default=str(DOSSIER / "script.json"))
    ap.add_argument("-o", "--sortie", help="fichier .mp4 de sortie (défaut : sortie/<nom du script>.mp4)")
    ap.add_argument("--apercu", action="store_true", help="rendu rapide en demi-résolution")
    ap.add_argument("--beats", action="store_true", help="affiche les temps des beats pour caler les paroles")
    args = ap.parse_args()

    cfg = charger_script(args.script)
    if not os.path.exists(cfg["musique"]):
        sys.exit(f"Musique introuvable : {cfg['musique']}\nMets ton fichier audio dans video/musique/ "
                 f"et indique son nom dans « musique » du script.")

    if args.beats:
        audio = analyser_audio(cfg)
        print(f"{audio['tempo']:.0f} BPM — temps des beats (en s, depuis « debut ») :")
        forts = set(np.round(audio["beats_forts"], 4))
        for k, b in enumerate(audio["beats"]):
            print(f"{b:7.2f}{'  ●' if round(b, 4) in forts else '   '}", end="\n" if k % 4 == 3 else "")
        print()
        return

    nom = Path(args.script).stem + ("_apercu" if args.apercu else "")
    sortie = Path(args.sortie) if args.sortie else DOSSIER / "sortie" / f"{nom}.mp4"
    generer(cfg, sortie, echelle=0.5 if args.apercu else 1.0, crf=26 if args.apercu else 18)


if __name__ == "__main__":
    main()
