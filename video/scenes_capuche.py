"""Scènes supplémentaires du thème « capuche » : une ambiance par phrase des paroles.

Chaque scène a un coefficient k (0 → 1 → 0) calculé par ThemeCapuche.k_scene ; les
fonctions ci-dessous sont appelées à différentes étapes du rendu d'une image :

    ciel        couleurs du ciel (coucher de soleil, aube, matin)
    avant_lune  étoiles
    sur_lune    horloge, phases, viseur / tir, rayons, ondes
    decor       palmiers, flammes, éclairs, regards, autres silhouettes (derrière le perso)
    sur_perso   fumée blanche + braise, cornes de démon, ondes de combat
    premier_plan  pièces, diamants, billets, cœurs, lettres Z, rayons divins, gyrophares
    post        noir et blanc, vieux film, projecteur, glitch, teinte police
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TOUS_EFFETS = (
    "vent", "ame_noire", "pare_brise", "yeux_rouges", "matrice", "sourire", "cicatrices", "peace",
    "horloge", "tempete", "palmiers", "flammes", "fumee_blanche", "tresor", "regards", "likes",
    "projecteur", "combat", "diamants", "nuit", "souvenirs", "demons", "aube", "gris", "silhouettes",
    "matin", "lumiere", "ondes", "billets", "lettres_z", "glitch", "gyrophares", "lune_tir", "phases",
)


def coller(dest, src, x, y):
    """alpha_composite qui accepte des positions hors de l'image."""
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w = min(src.width - sx, dest.width - dx)
    h = min(src.height - sy, dest.height - dy)
    if w > 0 and h > 0:
        dest.alpha_composite(src, (dx, dy), (sx, sy, sx + w, sy + h))


def _lisse(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _degrade(H, stops):
    """Dégradé vertical (H, 1, 3) à partir de [(position 0-1, (r, g, b)), ...]."""
    y = np.linspace(0, 1, H)
    pos = [p for p, _ in stops]
    col = np.stack([np.interp(y, pos, [c[k] for _, c in stops]) for k in range(3)], axis=1)
    return col.astype(np.float32)[:, None, :]


class ScenesCapuche:
    """Mixin ajouté à ThemeCapuche (utilise self.W, self.H, self.u, self.rouge, coller…)."""

    def _effets2(self, rng):
        u, W, H = self.u, self.W, self.H
        self.ciel_couchant = _degrade(H, [(0, (40, 10, 60)), (0.45, (150, 40, 90)), (0.68, (255, 120, 50)), (1, (20, 8, 12))])
        self.ciel_aube = _degrade(H, [(0, (60, 40, 70)), (0.5, (230, 140, 90)), (0.68, (255, 210, 130)), (1, (30, 20, 15))])
        self.ciel_matin = _degrade(H, [(0, (20, 30, 60)), (0.5, (70, 95, 140)), (0.68, (150, 170, 200)), (1, (15, 18, 25))])

        self.etoiles = np.column_stack([rng.random(140) * W, rng.random(140) * self.sol * 0.9,
                                        1 + rng.random(140) * 2.5, rng.random(140) * 6.28])
        # éclairs : 6 tracés pré-calculés
        self.eclairs = []
        for _ in range(6):
            x, y = (0.15 + rng.random() * 0.7) * W, 0.0
            pts = [(x, y)]
            while y < self.sol:
                y += (40 + rng.random() * 60) * u
                x += (rng.random() - 0.5) * 120 * u
                pts.append((x, y))
            self.eclairs.append(pts)
        # palmiers
        self.palmier = self._dessiner_palmier()
        # flammes
        self.fl_x = np.linspace(-0.05, 1.05, 34) + rng.random(34) * 0.02
        self.fl_ph = rng.random(34) * 6.28
        # pièces / diamants / billets / cœurs / Z : particules génériques
        n = 40
        self.pt_x, self.pt_y, self.pt_v = rng.random(n), rng.random(n), 0.12 + rng.random(n) * 0.2
        self.pt_ph, self.pt_t = rng.random(n) * 6.28, 0.6 + rng.random(n) * 0.8
        # regards dans l'ombre
        self.rg = [(rng.random() * W, (0.08 + rng.random() * 0.55) * H, 0.5 + rng.random() * 0.8, rng.random() * 3)
                   for _ in range(16)]
        self.rg = [p for p in self.rg if abs(p[0] - W / 2) > 260 * u or p[1] < 0.3 * H]
        # petites silhouettes (frères, cliquos)
        self.mini = []
        for ech, x, a in ((0.42, 0.13, 150), (0.5, 0.87, 170), (0.33, 0.30, 120), (0.36, 0.72, 130)):
            w, h = int(W * ech), int(self.sil_h * ech)
            c = self.corps.resize((w, h), Image.BILINEAR)
            c.putalpha(c.getchannel("A").point(lambda v, a=a: v * a // 255))
            self.mini.append((c, x * W, ech))
        # projecteur : masque lumineux en cône
        m = Image.new("L", (W // 4, H // 4), 40)
        d = ImageDraw.Draw(m)
        cx = W / 8
        d.polygon([(cx - 30 * u / 4, 0), (cx + 30 * u / 4, 0), (cx + 330 * u / 4, H / 4), (cx - 330 * u / 4, H / 4)], fill=255)
        m = m.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
        self.masque_projo = (np.asarray(m, np.float32) / 255)[..., None]
        # fissures de la lune
        self.fissures = []
        for _ in range(7):
            ang = rng.random() * 6.28
            pts, r = [(0.0, 0.0)], 0.0
            while r < 1.0:
                r += 0.12 + rng.random() * 0.1
                ang += (rng.random() - 0.5) * 0.7
                pts.append((math.cos(ang) * r, math.sin(ang) * r))
            self.fissures.append(pts)
        # fumée blanche
        f = np.asarray(self.fumee)
        blanc = f.copy()
        blanc[..., :3] = (200, 200, 210)
        blanc[..., 3] = (f[..., 3] * 0.45).astype(np.uint8)
        self.fumee_blanche = Image.fromarray(blanc, "RGBA")

    def _dessiner_palmier(self):
        u = self.u
        w, h = int(520 * u), int(1100 * u)
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        noir = (5, 3, 8, 255)
        # tronc courbé
        for k in range(60):
            f = k / 59
            x = w * 0.5 + math.sin(f * 1.6) * 90 * u
            y = h - f * h * 0.78
            r = (26 - 12 * f) * u
            d.ellipse((x - r, y - r, x + r, y + r), fill=noir)
        tx, ty = w * 0.5 + math.sin(1.6) * 90 * u, h - h * 0.78
        # palmes
        for a in np.linspace(-2.9, -0.25, 8):
            pts_h, pts_b = [], []
            for f in np.linspace(0, 1, 14):
                L = 240 * u * f
                droop = (f ** 2) * 120 * u
                x = tx + math.cos(a) * L
                y = ty + math.sin(a) * L + droop
                e = 22 * u * math.sin(f * math.pi)
                pts_h.append((x, y - e))
                pts_b.append((x, y + e))
            d.polygon(pts_h + pts_b[::-1], fill=noir)
        return img

    # ------------------------------------------------------------------ #

    def teinte_ciel(self, col, ks):
        for nom, cible, force in (("palmiers", self.ciel_couchant, 0.8), ("aube", self.ciel_aube, 0.75),
                                  ("matin", self.ciel_matin, 0.8)):
            k = ks[nom] * force
            if k > 0:
                col = col * (1 - k) + cible * k
        if ks["gris"] > 0:
            col = col * (1 - 0.5 * ks["gris"])
        return col

    def avant_lune(self, scene, t, ks):
        k = max(ks["nuit"], 0.5 * ks["outro"] if "outro" in ks else 0)
        if k <= 0:
            return
        d = ImageDraw.Draw(scene)
        for x, y, r, ph in self.etoiles:
            a = int(255 * k * (0.4 + 0.6 * abs(math.sin(t * 2 + ph))))
            r *= self.u
            d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 245, 250, a))
        # étoile filante
        p = (t * 0.4) % 1.0
        if p < 0.3:
            x0 = self.W * (0.9 - p * 2.4)
            y0 = self.H * (0.05 + p * 0.5)
            d.line((x0, y0, x0 + 160 * self.u, y0 - 70 * self.u), fill=(255, 255, 255, int(200 * k)), width=max(2, int(3 * self.u)))

    def sur_lune(self, scene, dlf, t, ks, ech, temps_scene):
        u = self.u
        cx, cy = self.lune_c
        R = self.lune_R * ech
        d = ImageDraw.Draw(scene)
        if ks["aube"] > 0 or ks["palmiers"] > 0:
            k = max(ks["aube"], ks["palmiers"])
            couleur = (255, 200, 90) if ks["aube"] >= ks["palmiers"] else (255, 150, 60)
            dlf.ellipse((cx - R, cy - R, cx + R, cy + R), fill=couleur + (int(170 * k),))
            if ks["aube"] > 0:
                for j in range(16):
                    a = j / 16 * 2 * math.pi + t * 0.2
                    dlf.line((cx + math.cos(a) * R * 1.1, cy + math.sin(a) * R * 1.1,
                              cx + math.cos(a) * R * 1.9, cy + math.sin(a) * R * 1.9),
                             fill=(255, 210, 120, int(150 * ks["aube"])), width=max(3, int(10 * u)))
        if ks["matin"] > 0:
            dlf.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(230, 235, 245, int(150 * ks["matin"])))
        if ks["horloge"] > 0:
            k = ks["horloge"]
            a = int(255 * k)
            c = (255, 235, 235)
            d.ellipse((cx - R * 0.92, cy - R * 0.92, cx + R * 0.92, cy + R * 0.92), outline=c + (a,), width=max(3, int(8 * u)))
            for j in range(12):
                ang = j / 12 * 2 * math.pi
                d.line((cx + math.cos(ang) * R * 0.78, cy + math.sin(ang) * R * 0.78,
                        cx + math.cos(ang) * R * 0.88, cy + math.sin(ang) * R * 0.88), fill=c + (a,), width=max(2, int(6 * u)))
            age = temps_scene.get("horloge", 0)
            for L, vit, ep in ((0.75, 7.0, 7), (0.5, 0.6, 11)):  # aiguilles qui s'emballent
                ang = -math.pi / 2 + age * vit
                d.line((cx, cy, cx + math.cos(ang) * R * L, cy + math.sin(ang) * R * L), fill=c + (a,), width=max(3, int(ep * u)))
                dlf.line((cx, cy, cx + math.cos(ang) * R * L, cy + math.sin(ang) * R * L), fill=self.rouge + (a,), width=max(4, int(ep * 2 * u)))
        if ks["phases"] > 0 or ks["nuit"] > 0:
            # ombre qui passe sur la lune : pleine → vide → pleine
            if ks["phases"] > 0:
                p = temps_scene.get("phases", 0) / max(temps_scene.get("phases_duree", 2), 0.5)
                dx = (p * 2.4 - 1.2) * R * 2
                k = ks["phases"]
            else:
                dx, k = R * 0.55, ks["nuit"]
            d.ellipse((cx - R + dx, cy - R * 1.02, cx + R + dx, cy + R * 1.02), fill=(4, 3, 6, int(245 * k)))
        if ks["lune_tir"] > 0:
            k = ks["lune_tir"]
            age = temps_scene.get("lune_tir", 0)
            t_tir = temps_scene.get("lune_tir_tir", 1.5)
            if age < t_tir:  # viseur qui se resserre
                rr = R * (1.6 - 0.6 * _lisse(age / t_tir))
                c = (255, 255, 255, int(220 * k))
                d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=c, width=max(2, int(5 * u)))
                for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    d.line((cx + sx * rr * 0.3, cy + sy * rr * 0.3, cx + sx * rr * 1.2, cy + sy * rr * 1.2), fill=c, width=max(2, int(5 * u)))
            else:
                ap = age - t_tir
                f = _lisse(ap / 0.15)
                for pts in self.fissures:
                    n = max(2, int(len(pts) * f))
                    p2 = [(cx + x * R, cy + y * R) for x, y in pts[:n]]
                    d.line(p2, fill=(20, 0, 0, int(255 * k)), width=max(3, int(9 * u)))
                    dlf.line(p2, fill=(255, 200, 150, int(200 * k * math.exp(-ap / 0.6))), width=max(4, int(16 * u)))
                if ap < 0.5:
                    g = R * (1 + ap * 3)
                    dlf.ellipse((cx - g, cy - g, cx + g, cy + g), outline=(255, 230, 200, int(255 * (1 - ap / 0.5))), width=max(4, int(20 * u)))
        if ks["ondes"] > 0:
            k = ks["ondes"]
            for j in range(6):
                p = (t * 0.5 + j / 6) % 1.0
                rr = R * (1.1 + p * 3.5)
                dlf.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=self.rouge + (int(200 * k * (1 - p)),), width=max(2, int(6 * u)))

    def decor(self, scene, t, ks, spec, fort, n_fort):
        u, W, H = self.u, self.W, self.H
        if ks["tempete"] > 0 and fort > 0.05:
            calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(calque)
            pts = self.eclairs[n_fort % len(self.eclairs)]
            a = int(255 * ks["tempete"] * fort)
            d.line(pts, fill=(200, 200, 255, a), width=max(4, int(18 * u)), joint="curve")
            self._briller(scene, calque)
            ImageDraw.Draw(scene).line(pts, fill=(255, 255, 255, a), width=max(2, int(5 * u)), joint="curve")
        if ks["palmiers"] > 0:
            k = _lisse(ks["palmiers"])
            p = self.palmier
            coller(scene, p, -60 * u, H - p.height + (1 - k) * 500 * u)
            pm = p.transpose(Image.FLIP_LEFT_RIGHT)
            coller(scene, pm, W - pm.width + 60 * u, H - pm.height * 0.92 + (1 - k) * 500 * u)
        if ks["flammes"] > 0:
            k = ks["flammes"]
            calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(calque)
            n = len(spec)
            for j, x in enumerate(self.fl_x):
                v = spec[min(n - 1, int(abs(x - 0.5) * 2 * n * 0.7))]
                h = (180 + 420 * v) * u * k * (0.8 + 0.2 * math.sin(t * 13 + self.fl_ph[j]))
                X = x * W
                w = 55 * u
                base = self.sol + 10 * u
                sway = math.sin(t * 7 + self.fl_ph[j]) * 25 * u
                for frac, col in ((1.0, (255, 60, 20)), (0.65, (255, 150, 40)), (0.35, (255, 230, 150))):
                    hh, ww = h * frac, w * frac
                    d.polygon([(X - ww, base), (X - ww * 0.4, base - hh * 0.5), (X + sway * frac, base - hh),
                               (X + ww * 0.4, base - hh * 0.5), (X + ww, base)], fill=col + (int(220 * k),))
            self._briller(scene, calque)
        if ks["regards"] > 0:
            d = ImageDraw.Draw(scene)
            k = ks["regards"]
            for x, y, e, ph in self.rg:
                ouvert = _lisse((k * 3 - ph * 0.5)) * (0.2 + 0.8 * abs(math.sin(t * 0.7 + ph)) ** 0.2)
                if ouvert <= 0.02:
                    continue
                for s in (-1, 1):
                    ex, ew, eh = x + s * 30 * u * e, 20 * u * e, 7 * u * e * ouvert
                    d.ellipse((ex - ew, y - eh, ex + ew, y + eh), fill=(255, 60, 60, int(255 * k)))
        if ks["silhouettes"] > 0:
            k = _lisse(ks["silhouettes"])
            d = ImageDraw.Draw(scene)
            for c, x, ech in self.mini:
                y = H - c.height + (1 - k) * 400 * u
                coller(scene, c, x - c.width / 2, y)
                for s in (-1, 1):
                    ex, ey = x + s * 54 * u * ech, y + 520 * u * ech
                    ew, eh = 17 * u * ech, 5 * u * ech
                    d.ellipse((ex - ew, ey - eh, ex + ew, ey + eh), fill=(255, 60, 60, int(220 * k)))

    def sur_perso(self, scene, dsc, dl, t, ks, ox, oy, sc, yeux, beats):
        u = self.u
        cx = (yeux[0][0] + yeux[1][0]) / 2
        ey = yeux[0][1]
        if ks["fumee_blanche"] > 0:
            k = ks["fumee_blanche"]
            bouche = (cx + 40 * u * sc, ey + 120 * u * sc)
            braise = 0.6 + 0.4 * abs(math.sin(t * 2.5))
            r = 8 * u * sc
            dsc.ellipse((bouche[0] - r, bouche[1] - r, bouche[0] + r, bouche[1] + r), fill=(255, 140, 40, int(255 * k * braise)))
            dl.ellipse((bouche[0] - r * 4, bouche[1] - r * 4, bouche[0] + r * 4, bouche[1] + r * 4), fill=(255, 120, 30, int(160 * k * braise)))
            for j in range(10):
                p = (self.f_ph[j] + t * 0.18) % 1.0
                x = bouche[0] + math.sin(t * 1.3 + j * 2) * 60 * u * p + self.f_dx[j] * 90 * u * p
                y = bouche[1] - p * 700 * u
                e = (0.4 + 1.4 * p) * sc
                img = self.fumee_blanche.resize((max(1, int(self.fumee.width * e)), max(1, int(self.fumee.height * e))), Image.BILINEAR)
                a = k * math.sin(p * math.pi)
                img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
                coller(scene, img, x - img.width / 2, y - img.height / 2)
        if ks["demons"] > 0:
            k = _lisse(ks["demons"])
            haut = oy + 140 * u * sc
            for s in (-1, 1):
                base = (cx + s * 120 * u * sc, haut + 120 * u * sc)
                pts_e, pts_i = [], []
                for f in np.linspace(0, 1, 12):
                    L = 260 * u * sc * k
                    x = base[0] + s * (math.sin(f * 1.8) * 0.55) * L
                    y = base[1] - f * L
                    e = 34 * u * sc * (1 - f)
                    pts_e.append((x + s * e, y))
                    pts_i.append((x - s * e, y))
                corne = pts_e + pts_i[::-1]
                dsc.polygon(corne, fill=(10, 4, 6, int(255 * k)))
                dl.line(corne + corne[:1], fill=self.rouge + (int(230 * k),), width=max(3, int(8 * u)))
        if ks["combat"] > 0 and len(beats):
            i = int(np.searchsorted(beats, t, side="right")) - 1
            if i >= 0:
                age = t - beats[i]
                if age < 0.45:
                    rr = age * 1800 * u
                    a = int(220 * ks["combat"] * (1 - age / 0.45))
                    dl.ellipse((cx - rr, ey - rr, cx + rr, ey + rr), outline=self.rouge + (a,), width=max(3, int(12 * u)))

    def premier_plan(self, scene, dl, t, ks, temps_scene):
        u, W, H = self.u, self.W, self.H
        d = ImageDraw.Draw(scene)
        n = len(self.pt_x)
        for nom in ("tresor", "diamants", "billets", "likes", "lettres_z"):
            k = ks[nom]
            if k <= 0:
                continue
            age = temps_scene.get(nom, 0)
            for j in range(n if nom != "lettres_z" else 14):
                if nom == "likes":  # cœurs qui montent depuis le bas à droite
                    p = ((age - j * 0.12) * 0.45) % 1.0 if age > j * 0.12 else -1
                    if p < 0:
                        continue
                    x = W * (0.82 + 0.1 * math.sin(p * 9 + j)) - j % 3 * 40 * u
                    y = H * (0.95 - p * 0.75)
                    s = (28 + 14 * (j % 3)) * u * (0.6 + 0.6 * min(1, p * 5))
                    a = int(255 * k * (1 - p))
                    col = (255, 40 + (j % 4) * 30, 90, a)
                    d.ellipse((x - s, y - s * 0.6, x, y + s * 0.3), fill=col)
                    d.ellipse((x, y - s * 0.6, x + s, y + s * 0.3), fill=col)
                    d.polygon([(x - s * 0.97, y), (x + s * 0.97, y), (x, y + s * 1.05)], fill=col)
                    continue
                y = ((self.pt_y[j] + age * self.pt_v[j] * (0.5 if nom == "lettres_z" else 1)) % 1.1 - 0.05)
                if nom == "lettres_z":
                    y = 1 - y
                x, y = self.pt_x[j] * W, y * H
                rot = math.sin(t * 3 * self.pt_t[j] + self.pt_ph[j])
                a = int(255 * k)
                if nom == "tresor":
                    r = 20 * u
                    w = max(2, r * abs(rot))
                    d.ellipse((x - w, y - r, x + w, y + r), fill=(255, 200, 60, a), outline=(180, 120, 20, a), width=max(1, int(3 * u)))
                    if j % 4 == 0:
                        g = 14 * u * abs(math.sin(t * 5 + j))
                        dl.line((x - g, y, x + g, y), fill=(255, 240, 180, a), width=max(2, int(3 * u)))
                        dl.line((x, y - g, x, y + g), fill=(255, 240, 180, a), width=max(2, int(3 * u)))
                elif nom == "diamants":
                    r = 24 * u * (0.7 + 0.5 * self.pt_t[j])
                    w = max(2, r * 0.7 * abs(rot))
                    pts = [(x, y - r), (x + w, y - r * 0.3), (x, y + r), (x - w, y - r * 0.3)]
                    d.polygon(pts, fill=(170, 235, 255, int(a * 0.85)), outline=(255, 255, 255, a))
                    dl.polygon(pts, fill=(120, 220, 255, int(a * 0.6)))
                elif nom == "billets":
                    bw, bh = 70 * u, 34 * u
                    ang = rot * 0.9 + self.pt_ph[j]
                    ca, sa = math.cos(ang), math.sin(ang) * (0.3 + 0.7 * abs(math.cos(t * 2 + j)))
                    coins = [(x + ca * dx - sa * dy, y + sa * dx + ca * dy) for dx, dy in
                             ((-bw, -bh), (bw, -bh), (bw, bh), (-bw, bh))]
                    d.polygon(coins, fill=(120, 165, 105, a), outline=(60, 90, 50, a))
                    d.text((x, y), "20", font=self.f_code, fill=(40, 70, 35, a), anchor="mm")
                else:  # lettres Z
                    img = self._texte("Z", self.f_lettres, self.rouge)
                    e = 0.35 + 0.5 * self.pt_t[j]
                    img = img.resize((max(1, int(img.width * e)), max(1, int(img.height * e))), Image.BILINEAR)
                    img.putalpha(img.getchannel("A").point(lambda v: int(v * k * 0.85)))
                    coller(scene, img, x - img.width / 2, y - img.height / 2)
        if ks["lumiere"] > 0 or ks["gyrophares"] > 0:
            # lumières diffuses : dessinées en petit puis floutées (pas de bords nets)
            pw, ph = W // 8, H // 8
            calque = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            dc = ImageDraw.Draw(calque)
            if ks["lumiere"] > 0:
                for j in range(4):
                    x = pw * (0.2 + j * 0.2) + math.sin(t * 0.4 + j) * 4
                    dc.polygon([(x - 2, 0), (x + 2, 0), (x + 22, ph * 0.7), (x + 6, ph * 0.7)],
                               fill=(255, 240, 210, int(70 * ks["lumiere"])))
            if ks["gyrophares"] > 0:
                phase = int(t * 5) % 2
                col = (255, 30, 40) if phase == 0 else (40, 80, 255)
                x = 0 if phase == 0 else pw
                dc.ellipse((x - pw * 0.45, ph * 0.3, x + pw * 0.45, ph * 0.9), fill=col + (int(170 * ks["gyrophares"]),))
            calque = calque.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)
            scene.alpha_composite(calque)
            scene.alpha_composite(calque)

    def post(self, arr, t, ks, i):
        W, H = self.W, self.H
        if ks["gris"] > 0:
            g = arr.mean(axis=2, keepdims=True)
            arr = arr * (1 - 0.85 * ks["gris"]) + g * 0.85 * ks["gris"]
        if ks["souvenirs"] > 0:
            k = ks["souvenirs"]
            g = arr.mean(axis=2, keepdims=True)
            sepia = g * np.array([1.15, 0.95, 0.7], np.float32)
            scintille = 0.9 + 0.1 * math.sin(t * 37) * math.sin(t * 23)
            arr = (arr * (1 - 0.8 * k) + sepia * 0.8 * k) * (1 - k + k * scintille)
            rng = np.random.default_rng(i)
            for _ in range(3):
                x = int(rng.random() * W)
                arr[:, x:x + max(1, W // 540)] = arr[:, x:x + max(1, W // 540)] * (1 - 0.6 * k) + 230 * 0.6 * k
        if ks["projecteur"] > 0:
            k = ks["projecteur"]
            arr = arr * (1 - k + k * self.masque_projo)
        if ks["gyrophares"] > 0:
            phase = int(t * 5) % 2
            teinte = np.array([1.25, 0.85, 0.85] if phase == 0 else [0.8, 0.9, 1.3], np.float32)
            arr = arr * (1 + (teinte - 1) * ks["gyrophares"])
        if ks["glitch"] > 0:
            k = ks["glitch"]
            rng = np.random.default_rng(int(t * 12))
            for _ in range(int(3 + 7 * k)):
                y0 = int(rng.random() * H)
                h = int((0.01 + rng.random() * 0.05) * H)
                dec = int((rng.random() - 0.5) * 160 * self.u * k)
                arr[y0:y0 + h] = np.roll(arr[y0:y0 + h], dec, axis=1)
            if rng.random() < 0.15 * k:
                y0 = int(rng.random() * H * 0.8)
                arr[y0:y0 + H // 12] = 255 - arr[y0:y0 + H // 12]
        return arr
