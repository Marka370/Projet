"""Bande-annonce « Ninja Legacy » : voix off + captures du jeu animées (format vertical).

Prérequis :
  1. la voix off : python ../voix_off.py voix_off.json --voix tom --vitesse 0.95
     → voix_off_tom.wav + voix_off_tom_chrono.json (temps de chaque phrase et de chaque mot)
  2. les captures du jeu dans captures/ (jeu_*.png = captures mobiles, les autres = captures PC)

    python montage.py                 # 1080×1920
    python montage.py --apercu        # 540×960, rapide

Chaque phrase de la voix off a sa scène : un écran (téléphone ou navigateur) dont la
caméra se déplace et zoome sur ce qui est dit, avec des encadrés qui s'allument au mot près.
"""

import argparse
import json
import math
import os
import subprocess
import sys
import wave
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ICI = Path(__file__).resolve().parent
POLICES = ICI.parent / "polices"
CAPTURES = ICI / "captures"

NOIR = (10, 10, 10)
ROUGE = (230, 57, 70)
BLEU = (0, 240, 255)
JAUNE = (255, 209, 102)
BLANC = (244, 244, 245)
GRIS = (161, 161, 170)
VERT = (52, 211, 153)


def lisse(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def sortie_rapide(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def rebond(x):
    x = min(max(x, 0.0), 1.0)
    c1, c3 = 1.7, 2.7
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def coller(dest, src, x, y):
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w = min(src.width - sx, dest.width - dx)
    h = min(src.height - sy, dest.height - dy)
    if w > 0 and h > 0:
        dest.alpha_composite(src, (dx, dy), (sx, sy, sx + w, sy + h))


def avec_alpha(img, a):
    if a >= 0.999:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


# --------------------------------------------------------------------------- #

class Montage:
    def __init__(self, chrono, echelle=1.0):
        self.e = e = echelle
        self.W, self.H = int(1080 * e) // 2 * 2, int(1920 * e) // 2 * 2
        self.chrono = chrono
        self.ph = {p["id"]: p for p in chrono["phrases"]}
        self.duree = chrono["duree"] + 3.0

        f = lambda nom, t: ImageFont.truetype(str(POLICES / nom), max(8, int(t * e)))
        self.f_titre = f("BebasNeue-Regular.ttf", 112)
        self.f_geant = f("BebasNeue-Regular.ttf", 230)
        self.f_kine = f("BebasNeue-Regular.ttf", 150)
        self.f_label = f("BebasNeue-Regular.ttf", 40)
        self.f_chip = f("BebasNeue-Regular.ttf", 34)
        self.f_sous = f("CrimsonText-SemiBold.ttf", 52)
        self.f_ital = f("CrimsonText-Italic.ttf", 50)
        self.f_petit = f("CrimsonText-Italic.ttf", 30)
        self.f_url = f("IBMPlexSans-Variable.ttf", 26)
        self.f_nombre = f("BebasNeue-Regular.ttf", 150)

        self._fond()
        self.cache = {}
        self.images = {}
        self.scenes = self._scenes()

    # ---------------- utilitaires temps ----------------
    def mot(self, pid, i):
        p = self.ph[pid]
        return p["mots"][min(i, len(p["mots"]) - 1)]

    def img(self, nom):
        if nom not in self.images:
            self.images[nom] = Image.open(CAPTURES / f"{nom}.png").convert("RGB")
        return self.images[nom]

    # ---------------- fond ----------------
    def _fond(self):
        W, H, e = self.W, self.H, self.e
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.95) / H) ** 2)
        lueur = np.clip(1 - d * 1.6, 0, 1) ** 2
        base = np.array(NOIR, np.float32) + lueur[..., None] * np.array([70, 10, 14], np.float32)
        vign = np.clip(1.25 - np.sqrt(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2), 0.45, 1)
        self.fond_arr = base * vign[..., None]
        rng = np.random.default_rng(1)
        self.grains = []
        for _ in range(4):
            g = rng.normal(0, 7, (H // 2 + 1, W // 2 + 1)).astype(np.float32)
            self.grains.append(np.repeat(np.repeat(g, 2, 0), 2, 1)[:H, :W, None])
        n = 46
        self.braises = np.column_stack([rng.random(n), rng.random(n), 0.02 + rng.random(n) * 0.04,
                                        1.5 + rng.random(n) * 3, rng.random(n) * 6.28])

    def dessiner_fond(self, t):
        img = Image.fromarray(self.fond_arr.astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(img)
        for x, y, v, r, ph in self.braises:
            yy = ((y - t * v) % 1.0) * self.H
            xx = (x + 0.02 * math.sin(t * 0.8 + ph)) * self.W
            a = int(110 + 90 * math.sin(t * 2 + ph))
            r *= self.e
            d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 90, 60, max(0, a)))
        return img

    # ---------------- éléments graphiques ----------------
    def texte_img(self, texte, police, couleur, contour=0, ligne=False):
        cle = (texte, police.path, police.size, couleur, contour, ligne)
        if cle not in self.cache and ligne:
            l, _, r, _ = police.getbbox(texte, stroke_width=contour)
            asc, desc = police.getmetrics()
            im = Image.new("RGBA", (r - l + 8, asc + desc + 8), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((4 - l, 4), texte, font=police, fill=couleur + (255,),
                                    stroke_width=contour, stroke_fill=(0, 0, 0, 255))
            self.cache[cle] = im
        if cle not in self.cache:
            l, t, r, b = police.getbbox(texte, stroke_width=contour)
            im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((4 - l, 4 - t), texte, font=police, fill=couleur + (255,),
                                    stroke_width=contour, stroke_fill=(0, 0, 0, 255))
            self.cache[cle] = im
        return self.cache[cle]

    def entete(self, calque, label, titre, t, t0, nouveau=False):
        """Petit label + grand titre en haut, qui glissent en entrant."""
        e = self.e
        p = sortie_rapide((t - t0) / 0.5)
        lab = self.texte_img(label.upper(), self.f_label, ROUGE)
        tit = self.texte_img(titre.upper(), self.f_titre, BLANC)
        x = self.W / 2
        dy = (1 - p) * 40 * e
        coller(calque, avec_alpha(lab, p), x - lab.width / 2, 120 * e + dy)
        # trait rouge sous le label
        d = ImageDraw.Draw(calque)
        lw = 70 * e * p
        d.line((x - lw, 175 * e + dy, x + lw, 175 * e + dy), fill=ROUGE + (int(255 * p),), width=max(2, int(3 * e)))
        p2 = sortie_rapide((t - t0 - 0.12) / 0.5)
        coller(calque, avec_alpha(tit, p2), x - tit.width / 2, 190 * e + (1 - p2) * 50 * e)
        if nouveau:
            p3 = rebond((t - t0 - 0.5) / 0.4)
            if p3 > 0:
                chip = self.chip("NOUVEAU · V1", JAUNE)
                c2 = chip.resize((max(1, int(chip.width * p3)), max(1, int(chip.height * p3))), Image.BILINEAR)
                coller(calque, c2, x - c2.width / 2, 78 * e - c2.height / 2)

    def chip(self, texte, couleur, plein=False):
        cle = ("chip", texte, couleur, plein)
        if cle not in self.cache:
            e = self.e
            tx = self.texte_img(texte, self.f_chip, NOIR if plein else couleur)
            w, h = tx.width + int(36 * e), tx.height + int(18 * e)
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 0, w - 1, h - 1), fill=couleur + (255,) if plein else (10, 10, 10, 220),
                        outline=couleur + (255,), width=max(2, int(3 * e)))
            im.alpha_composite(tx, ((w - tx.width) // 2, (h - tx.height) // 2))
            self.cache[cle] = im
        return self.cache[cle]

    # ---------------- écrans (téléphone / navigateur) ----------------
    def ecran(self, calque, nom, rect, cam, t, style="tel", reperes=(), alpha=1.0):
        """Affiche la capture `nom` dans un cadre, avec une caméra animée.

        cam : liste de (temps, cx, cy, zoom) en coordonnées de l'image ; zoom 1 = image à la
              largeur du cadre. reperes : liste de (boite x,y,w,h image, t_debut, couleur).
        """
        e = self.e
        X, Y, Wf, Hf = [v * e for v in rect]
        Wf, Hf = int(Wf), int(Hf)
        im = self.img(nom)
        cx, cy, z = self.camera(cam, t)
        if style == "tel":
            z *= 1.12
        s = Wf / im.width * z
        bw, bh = Wf / s, Hf / s
        # caméra bornée à l'image (fond noir si l'image est plus petite que le cadre)
        cx = min(max(cx, bw / 2), im.width - bw / 2) if bw < im.width else im.width / 2
        cy = min(max(cy, bh / 2), im.height - bh / 2) if bh < im.height else im.height / 2
        x0, y0 = cx - bw / 2, cy - bh / 2
        contenu = Image.new("RGB", (Wf, Hf), (12, 12, 13))
        bx0, by0 = max(0, x0), max(0, y0)
        bx1, by1 = min(im.width, x0 + bw), min(im.height, y0 + bh)
        if bx1 > bx0 and by1 > by0:
            part = im.resize((max(1, int((bx1 - bx0) * s)), max(1, int((by1 - by0) * s))), Image.BILINEAR,
                             box=(bx0, by0, bx1, by1))
            contenu.paste(part, (int((bx0 - x0) * s), int((by0 - y0) * s)))
        contenu = contenu.convert("RGBA")
        # encadrés qui s'allument
        d = ImageDraw.Draw(contenu)
        for (bx, by, bw2, bh2), tr, coul in reperes:
            if t < tr:
                continue
            p = sortie_rapide((t - tr) / 0.35)
            rx0, ry0 = (bx - x0) * s, (by - y0) * s
            rx1, ry1 = rx0 + bw2 * s, ry0 + bh2 * s
            ep = max(3, int(6 * e))
            # tracé qui fait le tour du cadre
            per = 2 * ((rx1 - rx0) + (ry1 - ry0))
            L = per * p
            pts = [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1), (rx0, ry0)]
            reste = L
            for (a, b) in zip(pts, pts[1:]):
                seg = math.dist(a, b)
                if reste <= 0:
                    break
                f = min(1, reste / seg) if seg else 1
                d.line((a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f), fill=coul + (255,), width=ep)
                reste -= seg
            if p >= 1:
                pulse = 0.5 + 0.5 * math.sin((t - tr) * 6)
                d.rectangle((rx0 - ep, ry0 - ep, rx1 + ep, ry1 + ep), outline=coul + (int(90 * pulse),), width=ep)
        # cadre
        rayon = int((46 if style == "tel" else 18) * e)
        haut = int(58 * e) if style == "nav" else 0
        total = Image.new("RGBA", (Wf, Hf + haut), (0, 0, 0, 0))
        if style == "nav":
            barre = Image.new("RGBA", (Wf, haut), (24, 24, 27, 255))
            db = ImageDraw.Draw(barre)
            for k, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
                r = 9 * e
                db.ellipse((26 * e + k * 30 * e - r, haut / 2 - r, 26 * e + k * 30 * e + r, haut / 2 + r), fill=c)
            db.rounded_rectangle((130 * e, haut * 0.2, Wf - 40 * e, haut * 0.8), radius=int(14 * e), fill=(10, 10, 11))
            url = self.texte_img("ninja-legacy  ·  jeu", self.f_url, GRIS)
            barre.alpha_composite(url, (int(150 * e), int((haut - url.height) / 2)))
            total.paste(barre, (0, 0))
        total.paste(contenu, (0, haut))
        masque = Image.new("L", total.size, 0)
        ImageDraw.Draw(masque).rounded_rectangle((0, 0, total.width - 1, total.height - 1), radius=rayon, fill=255)
        total.putalpha(masque)
        # ombre + lueur rouge
        marge = int(60 * e)
        ombre = Image.new("RGBA", (total.width + 2 * marge, total.height + 2 * marge), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).rounded_rectangle((marge, marge, marge + total.width, marge + total.height),
                                                radius=rayon, fill=(150, 20, 30, 120))
        ombre = ombre.filter(ImageFilter.GaussianBlur(28 * e))
        coller(calque, avec_alpha(ombre, alpha), X - marge, Y - marge)
        dt = ImageDraw.Draw(total)
        if style == "tel":
            dt.rounded_rectangle((0, 0, total.width - 1, total.height - 1), radius=rayon, outline=(40, 40, 44, 255), width=int(10 * e))
            dt.rounded_rectangle((Wf / 2 - 70 * e, 16 * e, Wf / 2 + 70 * e, 46 * e), radius=int(15 * e), fill=(0, 0, 0, 255))
        else:
            dt.rounded_rectangle((0, 0, total.width - 1, total.height - 1), radius=rayon, outline=(50, 50, 56, 255), width=max(1, int(2 * e)))
        coller(calque, avec_alpha(total, alpha), X, Y)

    @staticmethod
    def camera(cam, t):
        if t <= cam[0][0]:
            return cam[0][1:]
        for a, b in zip(cam, cam[1:]):
            if t <= b[0]:
                p = lisse((t - a[0]) / max(1e-6, b[0] - a[0]))
                return tuple(a[k] + (b[k] - a[k]) * p for k in (1, 2, 3))
        return cam[-1][1:]

    # ---------------- sous-titres ----------------
    def sous_titres(self, calque, t):
        e = self.e
        p = next((p for p in self.chrono["phrases"] if p["debut"] - 0.15 <= t <= p["fin"] + 0.35), None)
        if not p or p["id"] in ("intro", "fin"):
            return
        mots = p["texte"].split()
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        esp = d.textlength(" ", font=self.f_sous)
        largeur = self.W - 140 * e
        lignes, cour, lw = [], [], 0
        for i, m in enumerate(mots):
            w = d.textlength(m, font=self.f_sous)
            if cour and lw + esp + w > largeur:
                lignes.append((cour, lw))
                cour, lw = [], 0
            lw += (esp if cour else 0) + w
            cour.append((i, m, w))
        lignes.append((cour, lw))
        hl = self.f_sous.size * 1.22
        y = 1700 * e - (len(lignes) - 1) * hl / 2
        a = lisse((t - p["debut"] + 0.15) / 0.2) * (1 - lisse((t - p["fin"] - 0.15) / 0.2))
        # bandeau sombre derrière le texte
        bande = Image.new("RGBA", (self.W, int(hl * len(lignes) + 50 * e)), (0, 0, 0, int(150 * a)))
        bande = bande.filter(ImageFilter.GaussianBlur(10 * e))
        coller(calque, bande, 0, y - hl / 2 - 25 * e)
        for ligne, lw in lignes:
            x = (self.W - lw) / 2
            for i, m, w in ligne:
                tm = p["mots"][i]
                actif = tm <= t < (p["mots"][i + 1] if i + 1 < len(mots) else p["fin"] + 0.3)
                deja = t >= tm
                coul = ROUGE if actif else (BLANC if deja else (110, 110, 118))
                im = self.texte_img(m, self.f_sous, coul, contour=max(1, int(2 * e)), ligne=True)
                coller(calque, avec_alpha(im, a), x, y - im.height / 2)
                x += w + esp
            y += hl

    # ---------------- scènes ----------------
    def _scenes(self):
        M = self.mot
        ph = self.ph
        ids = [p["id"] for p in self.chrono["phrases"]]
        bornes = {}
        for k, i in enumerate(ids):
            debut = 0.0 if k == 0 else ph[i]["debut"] - 0.3
            fin = ph[ids[k + 1]]["debut"] - 0.3 if k + 1 < len(ids) else self.duree
            bornes[i] = [debut, fin]
        # l'intro garde le titre jusqu'à « c'est »
        bornes["intro"][1] = M("jeu", 2) - 0.1
        bornes["jeu"][0] = bornes["intro"][1]
        return bornes

    def scene(self, sid, calque, t):
        e = self.e
        M = self.mot
        t0, t1 = self.scenes[sid]
        TEL = (160, 360, 760, 1200)
        if sid == "intro":
            self.s_intro(calque, t)
        elif sid == "jeu":
            self.entete(calque, "Ninja Legacy", "Un RPG narratif", t, t0)
            self.ecran(calque, "jeu_landing", TEL, [(t0, 535, 760, 1.0), (M("jeu", 8), 535, 1100, 1.0), (t1, 535, 2050, 1.0)], t)
            if t >= M("jeu", 8):
                p = rebond((t - M("jeu", 8)) / 0.4)
                ch = self.chip("JOUABLE DANS TON NAVIGATEUR", ROUGE, plein=True)
                ch = ch.resize((max(1, int(ch.width * p)), max(1, int(ch.height * p))), Image.BILINEAR)
                coller(calque, ch, self.W / 2 - ch.width / 2, 1500 * e)
        elif sid == "creation":
            self.entete(calque, "Étape 1", "Crée ton ninja", t, t0)
            nom, boite, tr = "jeu_c1", (75, 640, 920, 110), M("creation", 3)
            if t >= M("creation", 5) - 0.1:
                nom, boite, tr = "jeu_c2", (90, 570, 920, 440), M("creation", 5)
            if t >= M("creation", 12) - 0.1:
                nom, boite, tr = "jeu_c3", (90, 570, 920, 430), M("creation", 12)
            self.ecran(calque, nom, TEL, [(t0, 535, 850, 1.0)], t, reperes=[(boite, tr, ROUGE)])
        elif sid == "naissance":
            self.entete(calque, "Dès le berceau", "Ta naissance", t, t0, nouveau=True)
            lignes = [(10, 52, 480, 40), (10, 97, 480, 40), (10, 142, 480, 40), (10, 187, 480, 40)]
            temps = [M("naissance", 6), M("naissance", 8), M("naissance", 10), M("naissance", 15)]
            cam = [(t0, 251, 117, 1.0), (temps[0], 251, 90, 1.25), (temps[2], 251, 150, 1.25), (t1, 251, 140, 1.1)]
            self.ecran(calque, "naissance", (70, 640, 940, 440), cam, t, style="nav",
                       reperes=[(b, tt, JAUNE if k == 3 else ROUGE) for k, (b, tt) in enumerate(zip(lignes, temps))])
        elif sid == "debut":
            self.entete(calque, "3 ans · Enfance", "Ta vie commence", t, t0)
            if t < M("debut", 8) - 0.1:
                self.ecran(calque, "jeu_game1", TEL, [(t0, 535, 850, 1.0), (M("debut", 8), 535, 800, 1.18)], t)
            else:
                self.ecran(calque, "jeu_ev05", TEL, [(M("debut", 8), 535, 850, 1.0), (t1, 535, 950, 1.0)], t,
                           reperes=[((70, 450, 930, 110), M("debut", 8), ROUGE)])
        elif sid == "choix":
            self.entete(calque, "Choix après choix", "Chaque choix compte", t, t0)
            c = [(107, 1256, 858, 369), (107, 1656, 858, 369), (107, 2057, 858, 296)]
            cam = [(t0, 535, 1000, 1.0), (M("choix", 4), 535, 1650, 1.0), (t1, 535, 1700, 1.0)]
            rep = [(c[0], M("choix", 5), ROUGE), (c[1], M("choix", 6), BLEU), (c[2], M("choix", 8), JAUNE)]
            self.ecran(calque, "jeu_ev05", TEL, cam, t, reperes=rep)
            for k, (txt, coul, tt) in enumerate((("PRUDENT", BLEU, M("choix", 6)), ("AUDACIEUX", JAUNE, M("choix", 8)))):
                if t >= tt:
                    p = rebond((t - tt) / 0.35)
                    ch = self.chip(txt, coul, plein=True)
                    ch = ch.resize((max(1, int(ch.width * p)), max(1, int(ch.height * p))), Image.BILINEAR)
                    coller(calque, ch, (300 if k == 0 else 780) * e - ch.width / 2, 1520 * e)
        elif sid == "trace":
            self.entete(calque, "Conséquences", "Tout laisse une trace", t, t0)
            if t < M("trace", 9) - 0.1:
                self.ecran(calque, "jeu_ev05_res", TEL, [(t0, 535, 1500, 1.0)], t,
                           reperes=[((60, 1590, 950, 470), t0 + 0.4, VERT)])
            else:
                self.ecran(calque, "jeu_stats", TEL, [(M("trace", 9), 535, 900, 1.0), (t1, 535, 1000, 1.05)], t,
                           reperes=[((50, 300, 970, 1060), M("trace", 9), ROUGE)])
                for k, (txt, coul, tt) in enumerate((("KARMA", ROUGE, M("trace", 11)), ("RÉPUTATION", JAUNE, M("trace", 13)))):
                    if t >= tt:
                        p = rebond((t - tt) / 0.35)
                        ch = self.chip(txt, coul, plein=True)
                        ch = ch.resize((max(1, int(ch.width * p)), max(1, int(ch.height * p))), Image.BILINEAR)
                        coller(calque, ch, (330 if k == 0 else 750) * e - ch.width / 2, 1500 * e)
        elif sid == "parchemin":
            self.entete(calque, "Techniques", "Le Parchemin Ninja", t, t0)
            cam = [(t0, 535, 900, 1.0), (M("parchemin", 8), 535, 1300, 1.0), (M("parchemin", 10), 535, 1900, 1.0), (t1, 535, 2500, 1.0)]
            self.ecran(calque, "jeu_tech", TEL, cam, t,
                       reperes=[((60, 1240, 950, 230), M("parchemin", 8), ROUGE)])
        elif sid == "missions":
            self.entete(calque, "Bureau officiel · Marché noir", "Pars en mission", t, t0, nouveau=t >= M("missions", 10) - 0.1)
            if t < M("missions", 10) - 0.15:
                self.ecran(calque, "jeu_missions", TEL, [(t0, 535, 850, 1.0), (M("missions", 6), 535, 1400, 1.0)], t,
                           reperes=[((60, 1050, 950, 700), M("missions", 6), ROUGE)])
            else:
                tm = M("missions", 10)
                cam = [(tm, 497, 470, 1.0), (M("missions", 12), 280, 470, 1.6), (t1, 280, 500, 1.7)]
                self.ecran(calque, "marche_noir", (50, 520, 980, 920), cam, t, style="nav",
                           reperes=[((191, 77, 84, 34), tm, ROUGE), ((85, 350, 390, 290), M("missions", 12), ROUGE),
                                    ((185, 505, 80, 35), M("missions", 16), JAUNE)])
        elif sid == "carrieres":
            self.entete(calque, "Une vie hors des combats", "Exerce un métier", t, t0, nouveau=True)
            cartes = [(50, 162, 390, 246), (50, 427, 390, 226), (458, 162, 390, 223), (458, 427, 390, 226), (50, 671, 390, 226)]
            temps = [M("carrieres", 7), M("carrieres", 8), M("carrieres", 9), M("carrieres", 11), M("carrieres", 13)]
            cam = [(t0, 440, 464, 1.0)]
            for (x, y, w, h), tt in zip(cartes, temps):
                cam.append((tt, x + w / 2, y + h / 2, 1.55))
            cam.append((t1, 440, 464, 1.0))
            self.ecran(calque, "carrieres", (70, 470, 940, 990), cam, t, style="nav",
                       reperes=[(b, tt, ROUGE) for b, tt in zip(cartes, temps)])
        elif sid == "mort":
            self.s_mort(calque, t, t0, t1)
        elif sid == "volontes":
            self.entete(calque, "Avant que la roue ne s'arrête", "Dernières volontés", t, t0, nouveau=True)
            rep = [((60, 135, 500, 40), M("volontes", 9), JAUNE), ((70, 255, 485, 40), M("volontes", 13), ROUGE),
                   ((70, 453, 485, 40), M("volontes", 17), ROUGE), ((70, 535, 485, 115), M("volontes", 21), ROUGE)]
            cam = [(t0, 306, 300, 1.0), (M("volontes", 13), 306, 290, 1.2), (M("volontes", 17), 306, 470, 1.2),
                   (M("volontes", 21), 306, 590, 1.2), (t1, 306, 600, 1.15)]
            self.ecran(calque, "volontes", (110, 400, 860, 1150), cam, t, style="nav", reperes=rep)
        elif sid == "flambeau":
            self.entete(calque, "Dynastie", "Passe le flambeau", t, t0, nouveau=True)
            rep = [((40, 170, 362, 45), M("flambeau", 6), ROUGE), ((60, 300, 345, 90), M("flambeau", 12), JAUNE),
                   ((245, 570, 155, 42), M("flambeau", 4), ROUGE)]
            cam = [(t0, 211, 314, 1.0), (M("flambeau", 4), 211, 420, 1.15), (M("flambeau", 6), 211, 230, 1.2),
                   (M("flambeau", 12), 211, 350, 1.2), (t1, 211, 314, 1.0)]
            self.ecran(calque, "flambeau", (170, 400, 740, 1100), cam, t, style="nav", reperes=rep)
        elif sid == "dynastie":
            self.s_dynastie(calque, t, t0, t1)
        elif sid == "fin":
            self.s_fin(calque, t, t0)

    # ---------------- scènes dessinées ----------------
    def logo(self, calque, cx, cy, taille, a):
        e = self.e
        L = taille * e
        im = Image.new("RGBA", (int(L * 1.6), int(L * 1.6)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = im.width / 2
        d.polygon([(c, c - L / 2 * 1.41), (c + L / 2 * 1.41, c), (c, c + L / 2 * 1.41), (c - L / 2 * 1.41, c)],
                  outline=ROUGE + (255,), width=max(2, int(L * 0.07)))
        r = L * 0.22
        d.polygon([(c, c - r), (c + r, c), (c, c + r), (c - r, c)], fill=ROUGE + (255,))
        coller(calque, avec_alpha(im, a), cx - im.width / 2, cy - im.height / 2)

    def coup_de_pinceau(self, calque, cy, p, a=1.0):
        """Trait d'encre rouge qui traverse l'écran."""
        if p <= 0:
            return
        e, W = self.e, self.W
        rng = np.random.default_rng(5)
        d = ImageDraw.Draw(calque)
        x1 = -60 * e + (W + 120 * e) * sortie_rapide(p)
        haut, bas = [], []
        for k, x in enumerate(np.linspace(-60 * e, x1, 40)):
            f = k / 39
            ep = (34 + 26 * math.sin(f * math.pi)) * e
            haut.append((x, cy - ep + rng.normal(0, 3) * e - 40 * e * (f - 0.5)))
            bas.append((x, cy + ep * 0.7 + rng.normal(0, 3) * e - 40 * e * (f - 0.5)))
        d.polygon(haut + bas[::-1], fill=(150, 20, 30, int(230 * a)))

    def s_intro(self, calque, t):
        e = self.e
        M = self.mot
        # question en typographie animée, mot par mot
        lignes = [("ET SI TU POUVAIS", [0, 1, 2, 3]), ("ÉCRIRE TA PROPRE", [4, 5, 6]), ("LÉGENDE", [7]), ("DE NINJA ?", [8, 9])]
        t_titre = M("intro", 10) + 0.35
        if t < t_titre:
            y = 560 * e
            for k, (txt, idx) in enumerate(lignes):
                tt = M("intro", idx[0])
                p = rebond((t - tt) / 0.3)
                if p > 0:
                    coul = ROUGE if k == 2 else BLANC
                    pol = self.f_geant if k == 2 else self.f_kine
                    im = self.texte_img(txt, pol, coul)
                    s = 0.6 + 0.4 * p
                    im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
                    coller(calque, avec_alpha(im2, min(1, p)), self.W / 2 - im2.width / 2, y + (im.height - im2.height) / 2)
                y += (250 if k == 2 else 175) * e
            if t > M("intro", 7):
                self.coup_de_pinceau(calque, 1240 * e, (t - M("intro", 7)) / 0.45, 0.5)
        else:
            p = (t - t_titre)
            self.coup_de_pinceau(calque, 960 * e, p / 0.35)
            self.logo(calque, self.W / 2, 700 * e, 110, lisse(p / 0.3))
            s = 1 + 1.2 * math.exp(-p / 0.07)
            for k, txt in enumerate(("NINJA", "LEGACY")):
                im = self.texte_img(txt, self.f_geant, BLANC if k == 0 else ROUGE, contour=max(2, int(4 * e)))
                im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
                coller(calque, avec_alpha(im2, min(1, p / 0.08)), self.W / 2 - im2.width / 2,
                       (880 + k * 210) * e - im2.height / 2 + 60 * e)
            tag = self.texte_img("Écris ta propre légende shinobi.", self.f_ital, ROUGE)
            coller(calque, avec_alpha(tag, lisse((p - 0.3) / 0.4)), self.W / 2 - tag.width / 2, 1300 * e)

    def s_mort(self, calque, t, t0, t1):
        e, W, H = self.e, self.W, self.H
        p = t - t0
        d = ImageDraw.Draw(calque)
        d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(235 * lisse(p / 0.25))))
        # fissures qui partent du centre
        rng = np.random.default_rng(11)
        tm = self.mot("mort", 3)
        f = sortie_rapide((t - tm) / 0.25)
        if f > 0:
            for _ in range(9):
                ang = rng.random() * 6.28
                pts, r = [(W / 2, 760 * e)], 0
                while r < 1:
                    r += 0.1 + rng.random() * 0.08
                    ang += (rng.random() - 0.5) * 0.8
                    pts.append((W / 2 + math.cos(ang) * r * 700 * e, 760 * e + math.sin(ang) * r * 900 * e))
                n = max(2, int(len(pts) * f))
                d.line(pts[:n], fill=ROUGE + (200,), width=max(2, int(5 * e)))
        if t >= tm:
            q = t - tm
            s = 1 + 0.8 * math.exp(-q / 0.06)
            im = self.texte_img("MORT", self.f_geant, ROUGE, contour=max(2, int(5 * e)))
            im2 = im.resize((int(im.width * s), int(im.height * s)), Image.BILINEAR)
            coller(calque, im2, W / 2 - im2.width / 2, 760 * e - im2.height / 2)
            sous = self.texte_img("DÉFINITIVE", self.f_kine, BLANC)
            coller(calque, avec_alpha(sous, lisse((t - self.mot("mort", 5)) / 0.3)), W / 2 - sous.width / 2, 900 * e)
            # bilan de la vie (capture « dernières volontés »)
            for k, (val, lab, coul) in enumerate(((43, "ÂGE À LA MORT", BLANC), (148, "ÉVÉNEMENTS", BLANC), (-244, "KARMA FINAL", ROUGE))):
                tk = tm + 0.5 + k * 0.25
                if t < tk:
                    continue
                v = int(val * sortie_rapide((t - tk) / 0.6))
                x = W / 2 + (k - 1) * 320 * e
                nb = self.texte_img(f"{v}" + (" ANS" if k == 0 else ""), self.f_kine, coul)
                coller(calque, nb, x - nb.width / 2, 1160 * e)
                lb = self.texte_img(lab, self.f_chip, GRIS)
                coller(calque, lb, x - lb.width / 2, 1330 * e)

    def s_dynastie(self, calque, t, t0, t1):
        e = self.e
        M = self.mot
        self.entete(calque, "Génération après génération", "Ta dynastie", t, t0)
        noeuds = [("Akira", "Gén. 0 · défunt", 540, 520, M("dynastie", 0), True),
                  ("Hana", "Gén. 1", 540, 820, M("dynastie", 2), False),
                  ("Ren", "Gén. 2", 300, 1120, M("dynastie", 7), False),
                  ("Sora", "Gén. 2", 780, 1120, M("dynastie", 7) + 0.2, False),
                  ("Kaito", "Gén. 3", 300, 1420, M("dynastie", 8) + 0.2, False)]
        liens = [(0, 1), (1, 2), (1, 3), (2, 4)]
        d = ImageDraw.Draw(calque)
        for a, b in liens:
            ta = noeuds[b][4]
            p = sortie_rapide((t - ta + 0.15) / 0.4)
            if p <= 0:
                continue
            x0, y0 = noeuds[a][2] * e, noeuds[a][3] * e + 80 * e
            x1, y1 = noeuds[b][2] * e, noeuds[b][3] * e - 80 * e
            ym = (y0 + y1) / 2
            pts = [(x0, y0), (x0, ym), (x1, ym), (x1, y1)]
            L = sum(math.dist(u, v) for u, v in zip(pts, pts[1:])) * p
            for u, v in zip(pts, pts[1:]):
                seg = math.dist(u, v)
                if L <= 0:
                    break
                f = min(1, L / seg) if seg else 1
                d.line((u[0], u[1], u[0] + (v[0] - u[0]) * f, u[1] + (v[1] - u[1]) * f), fill=ROUGE + (220,), width=max(2, int(4 * e)))
                L -= seg
        for nom, gen, x, y, tt, mort in noeuds:
            p = rebond((t - tt) / 0.4)
            if p <= 0:
                continue
            w, h = 360 * e * p, 150 * e * p
            X, Y = x * e - w / 2, y * e - h / 2
            d.rectangle((X, Y, X + w, Y + h), fill=(20, 12, 14, 240), outline=(ROUGE if not mort else (90, 90, 96)) + (255,), width=max(2, int(4 * e)))
            if p > 0.9:
                lab = self.texte_img("KONOHA · UCHIHA", self.f_url, VERT)
                coller(calque, lab, X + 24 * e, Y + 18 * e)
                n = self.texte_img(nom, self.f_label, ROUGE if not mort else GRIS)
                coller(calque, n, X + 24 * e, Y + 55 * e)
                g = self.texte_img(gen, self.f_url, GRIS)
                coller(calque, g, X + 24 * e, Y + 105 * e)

    def s_fin(self, calque, t, t0):
        e = self.e
        p = t - t0
        self.coup_de_pinceau(calque, 860 * e, p / 0.4)
        self.logo(calque, self.W / 2, 560 * e, 120, lisse(p / 0.3))
        s = 1 + 1.0 * math.exp(-p / 0.07)
        for k, txt in enumerate(("NINJA", "LEGACY")):
            im = self.texte_img(txt, self.f_geant, BLANC if k == 0 else ROUGE, contour=max(2, int(4 * e)))
            im2 = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
            coller(calque, avec_alpha(im2, min(1, p / 0.08)), self.W / 2 - im2.width / 2, (780 + k * 210) * e - im2.height / 2 + 60 * e)
        tm = self.mot("fin", 2)
        tag = self.texte_img("Mille destins t'attendent.", self.f_ital, BLANC)
        coller(calque, avec_alpha(tag, lisse((t - tm) / 0.4)), self.W / 2 - tag.width / 2, 1190 * e)
        td = self.mot("fin", 5)
        if t >= td:
            q = rebond((t - td) / 0.4)
            ch = self.chip("DISCORD  ·  discord.gg/ninjalegacy", ROUGE, plein=True)
            ch = ch.resize((max(1, int(ch.width * q * 1.3)), max(1, int(ch.height * q * 1.3))), Image.BILINEAR)
            coller(calque, ch, self.W / 2 - ch.width / 2, 1340 * e)
        mention = self.texte_img("Projet de fan indépendant, non affilié aux ayants droit de Naruto.", self.f_petit, (120, 120, 128))
        coller(calque, avec_alpha(mention, lisse((t - td - 0.5) / 0.5)), self.W / 2 - mention.width / 2, 1780 * e)

    # ---------------- image complète ----------------
    def image(self, i, fps):
        t = i / fps
        fond = self.dessiner_fond(t)
        actives = [(sid, a, b) for sid, (a, b) in self.scenes.items() if a - 0.01 <= t < b + 0.3]
        for sid, a, b in actives:
            calque = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
            self.scene(sid, calque, t)
            alpha = lisse((t - a) / 0.3) if a > 0 else 1.0
            if t > b:
                alpha *= 1 - lisse((t - b) / 0.3)
            fond.alpha_composite(avec_alpha(calque, alpha))
        self.sous_titres(fond, t)
        arr = np.asarray(fond.convert("RGB"), np.float32) + self.grains[i % 4]
        # fondu au noir à la toute fin
        arr *= 1 - lisse((t - (self.duree - 0.8)) / 0.8)
        return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


# --------------------------------------------------------------------------- #
# Musique d'ambiance (générée) + mixage
# --------------------------------------------------------------------------- #

def musique(duree, impacts, sr=44100):
    n = int(duree * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    # nappe grave : la mineur, change toutes les 8 s
    accords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (98.0, 123.47, 146.83), (82.41, 103.83, 123.47)]
    for k in range(int(duree // 8) + 1):
        a, b = int(k * 8 * sr), min(n, int((k + 1) * 8 * sr + sr))
        if a >= n:
            break
        tt = t[a:b] - k * 8
        env = np.minimum(1, tt / 1.5) * np.minimum(1, np.maximum(0, (9 - tt) / 1.5))
        nappe = sum(np.sin(2 * np.pi * f * tt) * 0.5 + np.sin(2 * np.pi * f * 2.003 * tt) * 0.15 for f in accords[k % 4])
        out[a:b] += nappe * env * 0.05
    out += np.sin(2 * np.pi * 55 * t) * 0.04 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.1 * t))
    # taikos sur les changements de scène
    for ti, force in impacts:
        a = int(ti * sr)
        if a >= n:
            continue
        L = min(n - a, int(1.2 * sr))
        tt = np.arange(L) / sr
        coup = np.sin(2 * np.pi * (48 * tt + 60 * (1 - np.exp(-tt * 25)) / 25)) * np.exp(-tt * 4)
        coup += np.random.default_rng(a).normal(0, 1, L) * np.exp(-tt * 40) * 0.25
        out[a:a + L] += coup * 0.45 * force
    fin = np.minimum(1, np.maximum(0, (duree - t) / 2.5))
    debut = np.minimum(1, t / 1.0)
    return (out * fin * debut).astype(np.float32)


def mixer(chrono_path, voix_path, scenes, duree, sortie_wav):
    with wave.open(str(voix_path)) as w:
        sr = w.getframerate()
        voix = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
    n = int(duree * sr)
    v = np.zeros(n, np.float32)
    v[:min(n, len(voix))] = voix[:n]
    impacts = [(a, 1.0) for sid, (a, b) in scenes.items() if a > 0]
    impacts.append((scenes["intro"][1] - 0.6, 1.4))
    impacts.append((scenes["mort"][0] + 1.1, 1.8))
    m = musique(duree, impacts, sr)
    # la musique baisse quand la voix parle
    env = np.convolve(np.abs(v), np.ones(int(0.3 * sr)) / int(0.3 * sr), mode="same")
    ducking = 1 - 0.45 * np.clip(env * 12, 0, 1)
    mix = v * 1.0 + m * ducking
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.95
    with wave.open(str(sortie_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())


# --------------------------------------------------------------------------- #

_M = None


def _init(chrono, echelle):
    global _M
    _M = Montage(chrono, echelle)


def _image(args):
    i, fps = args
    return _M.image(i, fps)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chrono", default=str(ICI / "voix_off_tom_chrono.json"))
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--image", type=float, help="rend une seule image au temps donné (PNG) pour vérifier")
    ap.add_argument("-o", "--sortie")
    args = ap.parse_args()

    chrono = json.loads(Path(args.chrono).read_text(encoding="utf-8"))
    echelle = 0.5 if args.apercu else 1.0
    m = Montage(chrono, echelle)
    if args.image is not None:
        data = m.image(int(args.image * args.fps), args.fps)
        out = Path(args.sortie or f"image_{args.image:.1f}.png")
        Image.frombytes("RGB", (m.W, m.H), data).save(out)
        print(out)
        return
    sortie = Path(args.sortie or ICI.parent / "sortie" / ("ninja_legacy_apercu.mp4" if args.apercu else "ninja_legacy.mp4"))
    sortie.parent.mkdir(parents=True, exist_ok=True)
    son = sortie.with_suffix(".wav")
    mixer(args.chrono, Path(args.chrono).with_name(chrono["audio"]), m.scenes, m.duree, son)
    n = int(m.duree * args.fps)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{m.W}x{m.H}",
           "-r", str(args.fps), "-i", "-", "-i", str(son), "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "26" if args.apercu else "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(sortie)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init, initargs=(chrono, echelle)) as pool:
        for k, data in enumerate(pool.imap(_image, [(i, args.fps) for i in range(n)], chunksize=4)):
            ff.stdin.write(data)
            if k % (args.fps * 5) == 0:
                print(f"\r  {k}/{n}", end="", flush=True)
    ff.stdin.close()
    ff.wait()
    son.unlink()
    print(f"\n✅ {sortie}")


if __name__ == "__main__":
    main()
