"""Thème « Capuche » : rue de nuit, silhouette encapuchonnée, lune rouge sang.

Éléments (tous synchronisés sur la musique) :
  - ciel noir → rouge, lune rouge qui pulse avec les basses, entourée d'un spectre
  - skyline dont les immeubles montent et descendent comme un égaliseur
  - silhouette à capuche, yeux rouges qui s'allument et flambent sur les impacts
  - pluie qui accélère avec les basses et passe au ralenti pendant la pause
  - impacts (« BANG »…) : mot qui s'écrase à l'écran, onde de choc, flash,
    tremblement, aberration chromatique
  - pause avant le drop : tout s'assombrit, zoom lent sur la capuche,
    le mot du drop s'écrit lettre par lettre
  - grain de film + vignette

Réglages dans le script JSON, clé « capuche » (temps en s depuis « debut ») :
    "capuche": {
        "apparition": 1.55,               # la silhouette sort du brouillard
        "pause": [7.73, 9.77],            # break avant le drop
        "impacts": [{"t": 3.08, "texte": "BANG"}, ...]
    }
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

POLICE_IMPACT = [
    "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf",
    "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def police(taille, chemins=POLICE_IMPACT):
    for c in chemins:
        try:
            return ImageFont.truetype(c, taille)
        except OSError:
            continue
    return ImageFont.load_default(taille)


def borne(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def lisse(x):
    x = borne(x)
    return x * x * (3 - 2 * x)


def coller(dest, src, x, y):
    """alpha_composite qui accepte des positions hors de l'image."""
    x, y = int(round(x)), int(round(y))
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w = min(src.width - sx, dest.width - dx)
    h = min(src.height - sy, dest.height - dy)
    if w > 0 and h > 0:
        dest.alpha_composite(src, (dx, dy), (sx, sy, sx + w, sy + h))


class ThemeCapuche:
    def __init__(self, r):
        self.r = r
        self.cfg = r.cfg
        self.audio = r.audio
        self.W, self.H = r.W, r.H
        self.u = u = r.W / 1080
        opts = self.cfg.get("capuche", {})
        self.apparition = float(opts.get("apparition", 1.5))
        self.pause = opts.get("pause")
        self.impacts = sorted(opts.get("impacts", []), key=lambda x: x["t"])
        self.t_impacts = np.array([x["t"] for x in self.impacts])

        self.rouge = r.c_acc
        self.cx = self.W / 2
        self.lune_c = (self.cx, self.H * 0.40)
        self.sol = self.H * 0.70

        rng = np.random.default_rng(3)
        self._ciel()
        self._lune(rng)
        self._immeubles(rng)
        self._silhouette()
        self._brouillard(rng)
        self._pluie(rng)
        self._grain(rng)

        self.f_impact = police(int(300 * u))
        self.f_titre = police(int(96 * u))
        self.f_lettres = police(int(150 * u))
        self.cache = {}

    # ------------------------------------------------------------------ #
    # Pré-calculs
    # ------------------------------------------------------------------ #

    def _briller(self, scene, calque):
        W, H = self.W, self.H
        petit = calque.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5))
        halo = petit.resize((W, H), Image.BILINEAR)
        scene.alpha_composite(halo)
        scene.alpha_composite(halo)
        scene.alpha_composite(calque)

    def _ciel(self):
        y = np.linspace(0, 1, self.H, dtype=np.float32)[:, None]
        haut = np.array([4, 3, 6], np.float32)
        horizon = np.array(self.rouge, np.float32) * 0.28
        bas = np.array([6, 4, 6], np.float32)
        k = np.clip(y / 0.68, 0, 1) ** 2.2
        col = haut * (1 - k) + horizon * k
        col = np.where(y > 0.68, horizon * (1 - (y - 0.68) / 0.32) + bas * ((y - 0.68) / 0.32), col)
        self.ciel = col[:, None, :]  # (H, 1, 3)

    def _lune(self, rng):
        u = self.u
        R = int(250 * u)
        taille = int(R * 3.4)
        c = taille / 2
        yy, xx = np.mgrid[0:taille, 0:taille].astype(np.float32)
        d = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / R
        rouge = np.array(self.rouge, np.float32)
        # disque + halo
        disque = np.clip((1.0 - d) * 40, 0, 1)
        halo = np.clip(np.exp(-(d - 1) * 2.2), 0, 1) * (d >= 1) * 0.55
        # cratères : bruit basse fréquence
        bruit = Image.fromarray((rng.random((12, 12)) * 255).astype(np.uint8)).resize(
            (taille, taille), Image.BICUBIC)
        bruit = np.asarray(bruit, np.float32) / 255
        teinte = rouge * (0.75 + 0.35 * bruit[..., None]) + np.array([60, 10, 10], np.float32) * (1 - d[..., None]) ** 2
        rgb = np.clip(teinte, 0, 255)
        alpha = np.clip(disque + halo, 0, 1)
        self.lune = Image.fromarray(np.dstack([rgb, alpha[..., None] * 255]).astype(np.uint8), "RGBA")
        self.lune_R = R

    def _immeubles(self, rng):
        u = self.u
        self.immeubles = []
        x = -40 * u
        n_bandes = self.audio["spectre"].shape[0]
        while x < self.W + 40 * u:
            w = int((70 + rng.random() * 90) * u)
            hmax = int(1000 * u)
            img = Image.new("RGBA", (w, hmax), (9, 8, 12, 255))
            d = ImageDraw.Draw(img)
            # fenêtres
            fw, fh, pas = int(10 * u), int(14 * u), int(26 * u)
            for fy in range(int(18 * u), hmax, pas):
                for fx in range(int(10 * u), w - fw - int(6 * u), int(22 * u)):
                    if rng.random() < 0.22:
                        chaud = rng.random() < 0.7
                        c = (255, 190, 90) if chaud else self.rouge
                        a = int(90 + rng.random() * 120)
                        d.rectangle((fx, fy, fx + fw, fy + fh), fill=c + (a,))
            # liseré rouge sur le toit
            d.line((0, 0, w, 0), fill=self.rouge + (180,), width=max(2, int(3 * u)))
            centre = (x + w / 2) / self.W
            if abs(x + w / 2 - self.W / 2) < 230 * u:
                x += w * 0.9
                continue
            bande = int(abs(centre - 0.5) * 2 * (n_bandes - 1) * 0.8)  # graves au centre
            self.immeubles.append({
                "img": img, "x": x, "base": (160 + rng.random() * 300) * u,
                "bande": min(bande, n_bandes - 1), "w": w,
            })
            x += w * (0.75 + rng.random() * 0.4)
        # les plus hauts derrière
        self.immeubles.sort(key=lambda b: -b["base"])

    def _silhouette(self):
        u, cx = self.u, self.W / 2
        h = int(self.H * 0.62)
        self.sil_h = h
        masque = Image.new("L", (self.W, h), 0)
        d = ImageDraw.Draw(masque)
        # épaules / torse
        d.ellipse((cx - 480 * u, 600 * u, cx + 480 * u, 1800 * u), fill=255)
        d.polygon([(cx - 210 * u, 560 * u), (cx + 210 * u, 560 * u), (cx + 360 * u, 820 * u), (cx - 360 * u, 820 * u)], fill=255)
        # capuche pointue
        pts = []
        for k in range(120):
            th = k / 120 * 2 * math.pi
            c = math.cos(th)
            px = cx + 240 * u * math.sin(th) * (1 - 0.08 * max(0, c))
            py = 470 * u - 340 * u * c * (1 + 0.22 * max(0, c) ** 3)
            pts.append((px, py))
        d.polygon(pts, fill=255)

        corps = Image.new("RGBA", (self.W, h), (16, 15, 19, 0))
        corps.putalpha(masque)
        # léger dégradé de matière sur le tissu
        tissu = np.zeros((h, self.W, 4), np.uint8)
        g = np.linspace(26, 10, h).astype(np.uint8)[:, None]
        tissu[..., 0] = g
        tissu[..., 1] = (g * 0.9).astype(np.uint8)
        tissu[..., 2] = (g * 1.1).astype(np.uint8)
        tissu[..., 3] = np.asarray(masque)
        corps = Image.fromarray(tissu, "RGBA")
        dc = ImageDraw.Draw(corps)
        # visage : trou noir dans la capuche
        dc.ellipse((cx - 128 * u, 330 * u, cx + 128 * u, 720 * u), fill=(2, 2, 3, 255))
        # pli de la capuche
        dc.arc((cx - 175 * u, 290 * u, cx + 175 * u, 790 * u), 200, 340, fill=(30, 28, 34, 255), width=int(14 * u))
        # cordons
        for sx in (-1, 1):
            dc.line((cx + sx * 70 * u, 700 * u, cx + sx * 84 * u, 990 * u), fill=(150, 150, 158, 255), width=max(3, int(7 * u)))
            dc.rectangle((cx + sx * 84 * u - 7 * u, 990 * u, cx + sx * 84 * u + 7 * u, 1030 * u), fill=(190, 190, 198, 255))
        self.corps = corps

        # contre-jour rouge (lumière de la lune sur le contour)
        petit = masque.resize((self.W // 2, h // 2))
        bord = np.asarray(petit, np.float32) - np.asarray(petit.filter(ImageFilter.MinFilter(9)), np.float32)
        bord *= np.linspace(1.0, 0.15, h // 2)[:, None]
        bord = Image.fromarray(np.clip(bord, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
        bord = bord.resize((self.W, h), Image.BILINEAR)
        lisere = Image.new("RGBA", (self.W, h), self.rouge + (0,))
        lisere.putalpha(bord)
        self.lisere = lisere

        self.yeux = [(cx - 54 * u, 520 * u), (cx + 54 * u, 520 * u)]

    def _brouillard(self, rng):
        w, h = self.W * 2, int(self.H * 0.45)
        b = Image.fromarray((rng.random((10, 40)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        b = np.asarray(b.filter(ImageFilter.GaussianBlur(20 * self.u)), np.float32) / 255
        fondu = np.sin(np.linspace(0, math.pi, h))[:, None] ** 1.5
        a = np.clip(b * fondu * 120, 0, 255).astype(np.uint8)
        img = np.zeros((h, w, 4), np.uint8)
        img[..., :3] = (60, 40, 48)
        img[..., 3] = a
        self.brouillard = Image.fromarray(img, "RGBA")

    def _pluie(self, rng):
        n = 260
        self.g_x = rng.random(n)
        self.g_y = rng.random(n)
        self.g_l = (30 + rng.random(n) * 70) * self.u
        self.g_v = 0.7 + rng.random(n) * 0.8
        self.g_a = (40 + rng.random(n) * 90).astype(int)
        fps = self.cfg["fps"]
        n_img = self.audio["n_images"]
        vitesse = np.empty(n_img)
        for i in range(n_img):
            vitesse[i] = (1 + 1.2 * self.audio["basses"][i]) * (1 - 0.85 * self._k_pause(i / fps))
        self.g_avance = np.cumsum(vitesse) / fps * 0.9

    def _grain(self, rng):
        h, w = self.H // 2, self.W // 2
        self.grains = []
        for _ in range(6):
            g = Image.fromarray(rng.integers(0, 255, (h, w), dtype=np.uint8)).resize((self.W, self.H), Image.NEAREST)
            self.grains.append(((np.asarray(g, np.int16) - 128) * 0.09).astype(np.float32)[..., None])

    # ------------------------------------------------------------------ #
    # Chronologie
    # ------------------------------------------------------------------ #

    def _k_pause(self, t):
        """0 hors pause, monte vers 1 pendant la pause, retombe net au drop."""
        if not self.pause:
            return 0.0
        a, b = self.pause
        if a <= t < b:
            return lisse((t - a) / 0.4)
        return 0.0

    def _impact(self, t):
        i = int(np.searchsorted(self.t_impacts, t, side="right")) - 1
        if i < 0:
            return None, 99.0, -1
        return self.impacts[i], t - self.impacts[i]["t"], i

    def _texte(self, mot, f, couleur, contour=0.06):
        cle = (mot, f.size, couleur)
        if cle not in self.cache:
            cw = max(2, int(f.size * contour))
            l, t, r, b = f.getbbox(mot, stroke_width=cw)
            img = Image.new("RGBA", (r - l + 10, b - t + 10), (0, 0, 0, 0))
            ImageDraw.Draw(img).text((5 - l, 5 - t), mot, font=f, fill=couleur + (255,),
                                     stroke_width=cw, stroke_fill=(0, 0, 0, 255))
            self.cache[cle] = img
        return self.cache[cle]

    # ------------------------------------------------------------------ #
    # Image
    # ------------------------------------------------------------------ #

    def image(self, i):
        r, u, W, H = self.r, self.u, self.W, self.H
        fps = self.cfg["fps"]
        duree = self.audio["duree"]
        t = i / fps
        from generer_video import impulsion
        pulse, _ = impulsion(t, self.audio["beats"], 0.14)
        fort, n_fort = impulsion(t, self.audio["beats_forts"], 0.10)
        basse = float(self.audio["basses"][i])
        spec = self.audio["spectre"][:, i]
        kp = self._k_pause(t)
        imp, age, n_imp = self._impact(t)
        k_imp = math.exp(-age / 0.22) if age < 3 else 0.0
        apparu = lisse((t - self.apparition) / 1.2)
        energie = (1 - 0.65 * kp)

        # 1. Ciel
        lum = (0.85 + 0.5 * basse + 0.4 * k_imp) * energie
        arr = np.broadcast_to(self.ciel * lum, (H, W, 3))
        scene = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        lueur_fond = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # ce qui brille derrière la silhouette
        lueur = Image.new("RGBA", (W, H), (0, 0, 0, 0))       # ce qui brille devant
        dlf = ImageDraw.Draw(lueur_fond)
        dl = ImageDraw.Draw(lueur)

        # 2. Lune + spectre autour
        ech = 1 + 0.05 * basse + 0.08 * k_imp + 0.06 * kp
        lw = int(self.lune.width * ech)
        lune = self.lune.resize((lw, lw), Image.BILINEAR)
        if energie < 1:
            lune.putalpha(lune.getchannel("A").point(lambda a: int(a * (0.45 + 0.55 * energie))))
        coller(scene, lune, self.lune_c[0] - lw / 2, self.lune_c[1] - lw / 2)
        R0 = self.lune_R * ech * 1.06
        n = len(spec)
        for k in range(2 * n):
            v = spec[k if k < n else 2 * n - 1 - k] * energie
            if v < 0.05:
                continue
            ang = -math.pi / 2 + k / (2 * n) * 2 * math.pi + t * 0.15
            l = v ** 1.5 * 150 * u
            ca, sa = math.cos(ang), math.sin(ang)
            x0, y0 = self.lune_c[0] + ca * R0, self.lune_c[1] + sa * R0
            dlf.line((x0, y0, x0 + ca * l, y0 + sa * l), fill=self.rouge + (200,), width=max(2, int(5 * u)))
        self._briller(scene, lueur_fond)

        # 3. Skyline égaliseur
        for b in self.immeubles:
            h = b["base"] + spec[b["bande"]] ** 1.3 * 320 * u * energie
            coller(scene, b["img"], b["x"], self.sol - h)
        dsc = ImageDraw.Draw(scene)
        dsc.rectangle((0, self.sol, W, H), fill=(6, 5, 7, 255))

        # 4. Brouillard qui défile
        dx = (t * 25 * u) % W
        coller(scene, self.brouillard, -dx, self.sol - self.brouillard.height * 0.55)

        # 5. Silhouette (zoom lent pendant la pause, respire avec les basses)
        if apparu > 0:
            sc = (1 + 0.015 * basse + 0.012 * pulse) * (1 + 0.16 * kp)
            w, h = int(W * sc), int(self.sil_h * sc)
            corps = self.corps.resize((w, h), Image.BILINEAR)
            lisere = self.lisere.resize((w, h), Image.BILINEAR)
            if apparu < 1:
                for c in (corps, lisere):
                    c.putalpha(c.getchannel("A").point(lambda a: int(a * apparu)))
            ox, oy = self.cx - w / 2, H - h + (1 - apparu) * 120 * u
            coller(scene, corps, ox, oy)
            coller(lueur, lisere, ox, oy)
            coller(lueur, lisere, ox, oy)

            # Yeux : s'allument au premier impact, flambent sur chaque impact
            premier = self.impacts[0]["t"] if self.impacts else self.apparition
            allume = lisse((t - premier) / 0.08) if t >= premier else 0.25 * apparu * (0.5 + 0.5 * math.sin(t * 9))
            intens = allume * (0.55 + 0.25 * pulse + 0.2 * basse) + 0.9 * k_imp
            if kp > 0:
                intens = max(intens, 0.4 + 0.6 * abs(math.sin(t * 3.2)))  # battement pendant la pause
            for ex, ey in self.yeux:
                x = ox + ex * sc
                y = oy + ey * sc
                ew, eh = 34 * u * sc, (9 + 2 * k_imp) * u * sc
                a = int(255 * borne(intens))
                dsc.ellipse((x - ew / 2, y - eh / 2, x + ew / 2, y + eh / 2), fill=(255, 70, 70, a))
                g = (36 + 50 * k_imp) * u
                dl.ellipse((x - g, y - g * 0.45, x + g, y + g * 0.45), fill=self.rouge + (int(200 * borne(intens)),))
            centre_yeux = (self.cx, oy + self.yeux[0][1] * sc)
        else:
            centre_yeux = (self.cx, H * 0.6)

        # 6. Onde de choc des impacts
        if age < 0.7:
            rr = age * 2600 * u
            ep = max(2, int(26 * u * (1 - age / 0.7)))
            a = int(255 * (1 - age / 0.7))
            for d in (dsc, dl):
                d.ellipse((centre_yeux[0] - rr, centre_yeux[1] - rr, centre_yeux[0] + rr, centre_yeux[1] + rr),
                          outline=(255, 90, 90, a), width=ep)

        # 7. Pluie
        dp = ImageDraw.Draw(scene)
        av = self.g_avance[i]
        ys = (self.g_y + av * self.g_v) % 1.2 - 0.1
        incl = 0.18
        for k in range(len(self.g_x)):
            x, y, l = self.g_x[k] * W, ys[k] * H, self.g_l[k] * (1 - 0.6 * kp)
            dp.line((x, y, x - l * incl, y - l), fill=(200, 190, 210, int(self.g_a[k] * energie)), width=max(1, int(2 * u)))

        # 8. Halo lumineux
        self._briller(scene, lueur)

        # 9. Caméra : zoom « punch » + tremblement
        secousse = k_imp + 0.35 * fort
        if secousse > 0.02:
            z = 1 + 0.07 * k_imp + 0.025 * fort
            rng = np.random.default_rng((n_imp + 1) * 1000 + n_fort + 1)
            ox, oy = rng.uniform(-1, 1, 2) * 34 * u * secousse
            cw, ch = W / z, H / z
            scene = scene.resize((W, H), Image.BILINEAR,
                                 box=((W - cw) / 2 + ox, (H - ch) / 2 + oy, (W + cw) / 2 + ox, (H + ch) / 2 + oy))

        arr = np.asarray(scene.convert("RGB"), np.float32) * (r.vignette ** 1.6)
        scene = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

        # 10. Textes
        self._titres(scene, t, duree)
        self._lettres_pause(scene, t)
        r.textes_paroles(scene, t, pulse)
        if imp is not None and age < 1.3:
            self._mot_impact(scene, imp["texte"], age)

        # 11. Post-traitement : flash, aberration chromatique, grain, fondus
        arr = np.asarray(scene.convert("RGB"), np.float32)
        flash = 0.4 * math.exp(-age / 0.07) if age < 0.5 else 0.0
        if flash > 0.01:
            arr = arr + (np.array([255, 200, 200], np.float32) - arr) * flash
        dec = int((22 * k_imp + 5 * fort) * u)
        if dec > 0:
            arr[..., 0] = np.roll(arr[..., 0], dec, axis=1)
            arr[..., 2] = np.roll(arr[..., 2], -dec, axis=1)
        arr += self.grains[i % len(self.grains)]
        noir = lisse(t / 0.35) * lisse((duree - t) / 0.6)
        arr *= noir
        return np.clip(arr, 0, 255).astype(np.uint8).tobytes()

    # ------------------------------------------------------------------ #
    # Textes
    # ------------------------------------------------------------------ #

    def _titres(self, img, t, duree):
        titre = self.cfg.get("titre") or ""
        if not titre:
            return
        premier = self.impacts[0]["t"] if self.impacts else 2.5
        # intro : lettres qui tombent une à une ; outro : le titre revient
        if t < premier:
            k_sortie = lisse((premier - t) / 0.25)
            self._titre_lettres(img, titre, t - 0.15, k_sortie)
        else:
            debut_outro = max(duree - 2.2, self.impacts[-1]["t"] + 1.25 if self.impacts else 0)
            if t > debut_outro:
                self._titre_lettres(img, titre, t - debut_outro, 1.0)

    def _titre_lettres(self, img, titre, age, alpha):
        f = self.f_titre
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        esp = 8 * self.u
        largeurs = [d.textlength(c, font=f) for c in titre]
        total = sum(largeurs) + esp * (len(titre) - 1)
        x = (self.W - total) / 2
        y = self.H * 0.17
        for k, c in enumerate(titre):
            a = age - k * 0.06
            if a > 0 and c.strip():
                p = lisse(a / 0.18)
                couleur = self.rouge if c in "x×" else (240, 236, 240)
                lettre = self._texte(c, f, couleur)
                lettre = lettre.copy()
                lettre.putalpha(lettre.getchannel("A").point(lambda v: int(v * p * alpha)))
                coller(img, lettre, x + largeurs[k] / 2 - lettre.width / 2, y - lettre.height / 2 - (1 - p) * 60 * self.u)
            x += largeurs[k] + esp

    def _lettres_pause(self, img, t):
        if not self.pause:
            return
        a, b = self.pause
        if not (a <= t < b):
            return
        suivant = next((x for x in self.impacts if x["t"] >= b - 0.05), None)
        if not suivant:
            return
        mot = suivant["texte"]
        f = self.f_lettres
        d = ImageDraw.Draw(Image.new("L", (1, 1)))
        esp = 18 * self.u
        larg = [d.textlength(c, font=f) for c in mot]
        total = sum(larg) + esp * (len(mot) - 1)
        x = (self.W - total) / 2
        pas = (b - a - 0.35) / max(len(mot), 1)
        for k, c in enumerate(mot):
            age = t - (a + 0.2 + k * pas)
            if age > 0:
                p = lisse(age / 0.12)
                lettre = self._texte(c, f, (235, 230, 235)).copy()
                lettre.putalpha(lettre.getchannel("A").point(lambda v: int(v * p * 0.9)))
                coller(img, lettre, x + larg[k] / 2 - lettre.width / 2, self.H * 0.17 - lettre.height / 2)
            x += larg[k] + esp

    def _mot_impact(self, img, mot, age):
        base = self._texte(mot, self.f_impact, (255, 255, 255), contour=0.05)
        # s'écrase de très grand à sa taille, puis s'efface
        ech = 1 + 1.4 * math.exp(-age / 0.05)
        ech *= 1 + 0.03 * math.sin(age * 40) * math.exp(-age / 0.2)
        largeur_max = self.W * 0.92
        ech *= min(1.0, largeur_max / base.width)
        alpha = borne(age / 0.03) * (1 - lisse((age - 0.85) / 0.45))
        w, h = int(base.width * ech), int(base.height * ech)
        mot_img = base.resize((w, h), Image.BILINEAR)
        cx, cy = self.W / 2, self.H * 0.17
        # copies rouge / cyan décalées (glitch) qui se recollent
        dec = 26 * self.u * math.exp(-age / 0.12)
        for couleur, sens in (((255, 30, 60), -1), ((0, 230, 255), 1)):
            c = Image.new("RGBA", mot_img.size, couleur + (0,))
            c.putalpha(mot_img.getchannel("A").point(lambda v: int(v * alpha * 0.8)))
            coller(img, c, cx - w / 2 + sens * dec, cy - h / 2)
        m = mot_img.copy()
        m.putalpha(m.getchannel("A").point(lambda v: int(v * alpha)))
        coller(img, m, cx - w / 2, cy - h / 2)
