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
        "impacts": [{"t": 3.08, "texte": "BANG"}, ...],
        "scenes": [{"debut": 4.6, "fin": 8.8, "effet": "vent"}, ...]
    }

Scènes disponibles (pour illustrer les paroles) :
    vent         rafales, pluie couchée, brouillard qui file
    ame_noire    fumée noire qui s'échappe de la capuche, la lune s'assombrit
    pare_brise   gouttes qui coulent sur l'écran, larmes rouges sous les yeux
    yeux_rouges  zoom sur les yeux qui brûlent, phares qui filent sur la route
    matrice      pluie de code rouge derrière la silhouette
    sourire      sourire lumineux dans l'ombre de la capuche, une larme
    cicatrices   griffures qui lacèrent l'écran (option "temps": [...])
    peace        la pluie s'arrête, la lune s'éclaircit, tout se calme
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from scenes_capuche import TOUS_EFFETS, ScenesCapuche, coller

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


class ThemeCapuche(ScenesCapuche):
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
        self.scenes = opts.get("scenes", [])
        self.position_paroles = 0.84

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
        self._effets(rng)
        self._effets2(rng)
        self._pluie(rng)
        self._grain(rng)

        self.f_impact = police(int(300 * u))
        self.f_titre = police(int(96 * u))
        self.f_lettres = police(int(150 * u))
        self.f_code = police(int(34 * u), ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"] + POLICE_IMPACT)
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
        halo *= np.clip((1.68 - d) / 0.5, 0, 1)  # s'éteint avant le bord de l'image
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
                "img": img, "x": x, "base": (90 + rng.random() * 230) * u,
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
        vent = np.empty(n_img)
        for i in range(n_img):
            t = i / fps
            kv, kpc = self.k_scene("vent", t), self.k_scene("peace", t)
            calme = max(self.k_scene("aube", t), self.k_scene("matin", t), self.k_scene("lumiere", t))
            vitesse[i] = ((1 + 1.2 * self.audio["basses"][i]) * (1 - 0.85 * self._k_pause(t))
                          * (1 + 0.8 * kv) * (1 - 0.75 * kpc) * (1 + 0.9 * self.k_scene("tempete", t))
                          * (1 - 0.6 * calme))
            vent[i] = 25 + 700 * kv
        self.g_avance = np.cumsum(vitesse) / fps * 0.9
        self.brouillard_x = np.cumsum(vent) / fps * self.u

    def _effets(self, rng):
        u = self.u
        # vent : traînées horizontales
        self.v_x, self.v_y = rng.random(14), 0.15 + rng.random(14) * 0.75
        self.v_l, self.v_v = (200 + rng.random(14) * 400) * u, 1.2 + rng.random(14) * 1.5
        # âme noire : fumée
        r = int(130 * u)
        yy, xx = np.mgrid[-r:r, -r:r]
        a = np.clip(1 - np.sqrt(xx ** 2 + yy ** 2) / r, 0, 1) ** 1.2 * 245
        img = np.zeros((2 * r, 2 * r, 4), np.uint8)
        img[..., :3] = (0, 0, 0)
        img[..., 3] = a.astype(np.uint8)
        self.fumee = Image.fromarray(img, "RGBA")
        self.f_dx, self.f_ph = (rng.random(26) - 0.5) * 2, rng.random(26)
        # pare-brise : gouttes sur l'écran
        n = 28
        self.d_x, self.d_y = rng.random(n), rng.random(n)
        self.d_r, self.d_v = (8 + rng.random(n) * 16) * u, 0.05 + rng.random(n) * 0.22
        # yeux rouges : phares sur la route
        self.p_y = rng.random(12)
        self.p_ph, self.p_v = rng.random(12), 1.5 + rng.random(12) * 2
        self.p_l, self.p_rouge = (300 + rng.random(12) * 500) * u, rng.random(12) < 0.65
        # matrice : colonnes de code
        self.m_col = 24
        self.m_ph, self.m_v = rng.random(self.m_col), 0.25 + rng.random(self.m_col) * 0.35
        self.m_chars = "01ABCDEFXZ7#$%&<>"
        # cicatrices : griffures en zigzag
        self.griffes = []
        for k in range(3):
            x0 = (0.1 + 0.25 * k + rng.random() * 0.1) * self.W
            pts = []
            for j in range(13):
                f = j / 12
                pts.append((x0 + f * 0.45 * self.W + (rng.random() - 0.5) * 22 * u,
                            (0.12 + f * 0.6) * self.H + (rng.random() - 0.5) * 22 * u))
            self.griffes.append(pts)

    def k_scene(self, effet, t, entree=0.3, sortie=0.4):
        k = 0.0
        for sc in self.scenes:
            if sc["effet"] != effet:
                continue
            a, b = sc["debut"], sc["fin"]
            if a <= t <= b + sortie:
                k = max(k, lisse((t - a) / entree) * (1 - lisse((t - b) / sortie)))
        return k

    def _scene(self, effet, t):
        return next((sc for sc in self.scenes if sc["effet"] == effet and sc["debut"] <= t <= sc["fin"] + 0.4), None)

    def _grain(self, rng):
        h, w = self.H // 2, self.W // 2
        self.grains = []
        for _ in range(6):
            g = Image.fromarray(rng.integers(0, 255, (h, w), dtype=np.uint8)).resize((self.W, self.H), Image.NEAREST)
            self.grains.append(((np.asarray(g, np.int16) - 128) * float(self.cfg.get("grain", 0.09))).astype(np.float32)[..., None])

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
        ks = {e: self.k_scene(e, t) for e in TOUS_EFFETS}
        temps_scene = {}
        for e, k in ks.items():
            if k > 0:
                sc_e = self._scene(e, t)
                if sc_e:
                    temps_scene[e] = t - sc_e["debut"]
                    temps_scene[e + "_duree"] = sc_e["fin"] - sc_e["debut"]
                    temps_scene[e + "_tir"] = sc_e.get("tir", 1.5)
        if imp is not None and not imp.get("fort", True):
            k_imp_fort = 0.0
        else:
            k_imp_fort = k_imp
        energie = (1 - 0.65 * kp) * (1 - 0.45 * ks["ame_noire"])
        # griffures : chaque coup de griffe secoue l'écran
        k_griffe, n_griffe, t_griffes = 0.0, -1, []
        sc_g = self._scene("cicatrices", t)
        if sc_g:
            t_griffes = sc_g.get("temps") or [sc_g["debut"] + 0.5 * j for j in range(3)]
            k_griffe, n_griffe = impulsion(t, np.array(t_griffes), 0.12)

        # 1. Ciel
        lum = (0.85 + 0.5 * basse + 0.4 * k_imp_fort + 0.9 * fort * ks["tempete"]) * energie
        arr = np.broadcast_to(self.teinte_ciel(self.ciel * lum, ks), (H, W, 3))
        scene = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        lueur_fond = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # ce qui brille derrière la silhouette
        lueur = Image.new("RGBA", (W, H), (0, 0, 0, 0))       # ce qui brille devant
        dlf = ImageDraw.Draw(lueur_fond)
        dl = ImageDraw.Draw(lueur)

        self.avant_lune(scene, t, ks)

        # 2. Lune + spectre autour
        ech = 1 + 0.05 * basse + 0.08 * k_imp + 0.06 * kp
        lw = int(self.lune.width * ech)
        lune = self.lune.resize((lw, lw), Image.BILINEAR)
        if energie < 1:
            lune.putalpha(lune.getchannel("A").point(lambda a: int(a * (0.45 + 0.55 * energie))))
        coller(scene, lune, self.lune_c[0] - lw / 2, self.lune_c[1] - lw / 2)
        if ks["peace"] > 0:
            g = self.lune_R * ech * 0.95
            dlf.ellipse((self.lune_c[0] - g, self.lune_c[1] - g, self.lune_c[0] + g, self.lune_c[1] + g),
                        fill=(255, 225, 225, int(110 * ks["peace"])))
        self.sur_lune(scene, dlf, t, ks, ech, temps_scene)
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
            h = b["base"] + spec[b["bande"]] ** 1.3 * 260 * u * energie
            coller(scene, b["img"], b["x"], self.sol - h)
        dsc = ImageDraw.Draw(scene)
        dsc.rectangle((0, self.sol, W, H), fill=(6, 5, 7, 255))
        if ks["matrice"] > 0:
            self._matrice(scene, t, ks["matrice"])
        self.decor(scene, t, ks, spec, fort, n_fort)

        # 4. Brouillard qui défile
        dx = self.brouillard_x[i] % W
        coller(scene, self.brouillard, -dx, self.sol - self.brouillard.height * 0.55)

        # 5. Silhouette (zoom lent pendant la pause, respire avec les basses)
        apparu *= 1 - 0.7 * ks["matin"]
        if apparu > 0:
            sc = (1 + 0.015 * basse + 0.012 * pulse) * (1 + 0.16 * kp) * (1 + 0.14 * lisse(ks["yeux_rouges"]))
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
            intens = max(intens, ks["yeux_rouges"] * (0.9 + 0.1 * pulse))
            intens *= 1 - 0.5 * ks["peace"]
            for ex, ey in self.yeux:
                x = ox + ex * sc
                y = oy + ey * sc
                ew, eh = 34 * u * sc, (9 + 2 * k_imp) * u * sc
                a = int(255 * borne(intens))
                dsc.ellipse((x - ew / 2, y - eh / 2, x + ew / 2, y + eh / 2), fill=(255, 70, 70, a))
                g = (36 + 50 * k_imp + 28 * ks["yeux_rouges"]) * u
                dl.ellipse((x - g, y - g * 0.32, x + g, y + g * 0.32), fill=self.rouge + (int(200 * borne(intens)),))
            centre_yeux = (self.cx, oy + self.yeux[0][1] * sc)
            yeux = [(ox + ex * sc, oy + ey * sc) for ex, ey in self.yeux]
            if ks["ame_noire"] > 0:
                self._fumee(scene, t, centre_yeux, ks["ame_noire"], sc)
            if ks["pare_brise"] > 0:
                sc_pb = self._scene("pare_brise", t)
                self._larmes(dsc, dl, yeux, t - sc_pb["debut"] if sc_pb else 9, ks["pare_brise"], sc, (255, 40, 60))
            self.sur_perso(scene, dsc, dl, t, ks, ox, oy, sc, yeux, self.audio["beats"])
            if ks["sourire"] > 0:
                self._sourire(dsc, dl, yeux, ks["sourire"], sc)
                sc_s = self._scene("sourire", t)
                self._larmes(dsc, dl, yeux[:1], t - sc_s["debut"] if sc_s else 9, ks["sourire"], sc, (170, 210, 255))
        else:
            centre_yeux = (self.cx, H * 0.6)

        # 6. Onde de choc des impacts
        if age < 0.7 and k_imp_fort > 0:
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
        incl = 0.18 + 0.85 * ks["vent"]
        a_pluie = energie * (1 - 0.85 * ks["peace"])
        for k in range(len(self.g_x)):
            x, y, l = self.g_x[k] * W, ys[k] * H, self.g_l[k] * (1 - 0.6 * kp)
            dp.line((x, y, x - l * incl, y - l), fill=(200, 190, 210, int(self.g_a[k] * a_pluie)), width=max(1, int(2 * u)))
        if ks["vent"] > 0:
            self._vent(dp, t, ks["vent"])
        if ks["yeux_rouges"] > 0:
            self._phares(dl, t, ks["yeux_rouges"])
        if t_griffes:
            self._griffes(dsc, dl, t, t_griffes, ks["cicatrices"])
        self.premier_plan(scene, dl, t, ks, temps_scene)

        # 8. Halo lumineux
        self._briller(scene, lueur)

        # 9. Caméra : zoom « punch » + tremblement
        secousse = k_imp_fort + 0.35 * fort + 0.8 * k_griffe + 0.3 * pulse * ks["combat"]
        if secousse > 0.02:
            z = 1 + 0.07 * k_imp_fort + 0.025 * fort + 0.04 * k_griffe + 0.02 * pulse * ks["combat"]
            rng = np.random.default_rng((n_imp + 1) * 100000 + (n_griffe + 1) * 1000 + n_fort + 1)
            cw, ch = W / z, H / z
            ox, oy = np.clip(rng.uniform(-1, 1, 2) * 34 * u * secousse,
                             [-(W - cw) / 2, -(H - ch) / 2], [(W - cw) / 2, (H - ch) / 2])
            scene = scene.resize((W, H), Image.BILINEAR,
                                 box=((W - cw) / 2 + ox, (H - ch) / 2 + oy, (W + cw) / 2 + ox, (H + ch) / 2 + oy))

        arr = np.asarray(scene.convert("RGB"), np.float32) * (r.vignette ** 1.6)
        arr = self.post(arr, t, ks, i)
        scene = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

        if ks["pare_brise"] > 0:
            self._gouttes(scene, t, ks["pare_brise"])

        # 10. Textes
        self._titres(scene, t, duree)
        self._lettres_pause(scene, t)
        r.textes_paroles(scene, t, pulse)
        if imp is not None and age < 1.3:
            self._mot_impact(scene, imp["texte"], age)

        # 11. Post-traitement : flash, aberration chromatique, grain, fondus
        arr = np.asarray(scene.convert("RGB"), np.float32)
        flash = 0.4 * math.exp(-age / 0.07) if age < 0.5 and k_imp_fort > 0 else 0.0
        if flash > 0.01:
            arr = arr + (np.array([255, 200, 200], np.float32) - arr) * flash
        dec = int((22 * k_imp_fort + 5 * k_imp + 5 * fort + 18 * k_griffe) * u)
        if dec > 0:
            arr[..., 0] = np.roll(arr[..., 0], dec, axis=1)
            arr[..., 2] = np.roll(arr[..., 2], -dec, axis=1)
        arr += self.grains[i % len(self.grains)]
        noir = lisse(t / 0.35) * lisse((duree - t) / 0.6)
        arr *= noir
        return np.clip(arr, 0, 255).astype(np.uint8).tobytes()

    # ------------------------------------------------------------------ #
    # Effets des scènes
    # ------------------------------------------------------------------ #

    def _vent(self, d, t, k):
        u, W, H = self.u, self.W, self.H
        for j in range(len(self.v_x)):
            x = ((self.v_x[j] + t * self.v_v[j]) % 1.6 - 0.3) * W
            y = self.v_y[j] * H + math.sin(t * 3 + j) * 20 * u
            l = self.v_l[j]
            pts = [(x - l * f, y + math.sin(f * 6 + t * 4 + j) * 14 * u) for f in np.linspace(0, 1, 8)]
            d.line(pts, fill=(220, 215, 230, int(70 * k)), width=max(1, int(3 * u)))

    def _fumee(self, scene, t, centre, k, sc):
        u = self.u
        for j in range(len(self.f_dx)):
            p = (self.f_ph[j] + t * 0.22) % 1.0
            x = centre[0] + self.f_dx[j] * (120 + 260 * p) * u + math.sin(t * 1.5 + j) * 30 * u
            y = centre[1] + 120 * u - p * 1000 * u
            e = (0.6 + 1.6 * p) * sc
            img = self.fumee.resize((int(self.fumee.width * e), int(self.fumee.height * e)), Image.BILINEAR)
            a = k * math.sin(p * math.pi)
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
            coller(scene, img, x - img.width / 2, y - img.height / 2)

    def _larmes(self, d, dl, yeux, age, k, sc, couleur):
        u = self.u
        l = min(1.0, age / 1.4) * 260 * u * sc
        for x, y in yeux:
            y0 = y + 8 * u * sc
            pts = [(x + math.sin(f * 5) * 6 * u, y0 + f * l) for f in np.linspace(0, 1, 10)]
            a = int(230 * k)
            d.line(pts, fill=couleur + (a,), width=max(2, int(5 * u)))
            dl.line(pts, fill=couleur + (int(a * 0.8),), width=max(3, int(10 * u)))
            gx, gy = pts[-1]
            r = 9 * u
            d.ellipse((gx - r, gy - r * 0.6, gx + r, gy + r * 1.4), fill=couleur + (a,))

    def _sourire(self, d, dl, yeux, k, sc):
        u = self.u
        cx = (yeux[0][0] + yeux[1][0]) / 2
        y = yeux[0][1]
        w = 82 * u * sc
        boite = (cx - w, y - 40 * u * sc, cx + w, y + 105 * u * sc)
        a = int(255 * k)
        d.arc(boite, 25, 155, fill=(255, 235, 235, a), width=max(3, int(8 * u)))
        dl.arc(boite, 25, 155, fill=self.rouge + (a,), width=max(4, int(20 * u)))

    def _gouttes(self, scene, t, k):
        u, W, H = self.u, self.W, self.H
        d = ImageDraw.Draw(scene)
        for j in range(len(self.d_x)):
            # glisse par à-coups, comme une vraie goutte sur une vitre
            avance = t * self.d_v[j] + 0.04 * math.sin(t * 2.3 + j * 1.7)
            y = ((self.d_y[j] + avance) % 1.15 - 0.05) * H
            x = self.d_x[j] * W + math.sin(y / (90 * u) + j) * 6 * u
            r = self.d_r[j]
            trainee = r * 9
            d.line((x, y - trainee, x, y), fill=(210, 210, 230, int(45 * k)), width=max(2, int(r * 0.7)))
            d.ellipse((x - r, y - r, x + r, y + r * 1.2), fill=(150, 150, 175, int(70 * k)),
                      outline=(235, 235, 250, int(150 * k)), width=max(1, int(2 * u)))
            d.ellipse((x - r * 0.45, y - r * 0.6, x - r * 0.05, y - r * 0.2), fill=(255, 255, 255, int(190 * k)))

    def _phares(self, dl, t, k):
        u, W = self.u, self.W
        for j in range(len(self.p_y)):
            x = ((self.p_ph[j] + t * self.p_v[j] * 0.5) % 1.8 - 0.4) * W
            y = self.sol + 30 * u + self.p_y[j] * (self.H - self.sol - 60 * u)
            c = self.rouge if self.p_rouge[j] else (255, 240, 220)
            dl.line((x, y, x + self.p_l[j], y), fill=c + (int(200 * k),), width=max(2, int(6 * u)))

    def _matrice(self, scene, t, k):
        u, W, H = self.u, self.W, self.H
        d = ImageDraw.Draw(scene)
        pas = 40 * u
        largeur = W / self.m_col
        tic = int(t * 12)
        for c in range(self.m_col):
            tete = ((self.m_ph[c] + t * self.m_v[c]) % 1.4 - 0.2) * H
            x = (c + 0.5) * largeur
            for j in range(16):
                y = tete - j * pas
                if y < -pas or y > self.sol + 40 * u:
                    continue
                car = self.m_chars[(c * 31 + j * 7 + tic * (1 if j < 2 else 0) + int(y / pas)) % len(self.m_chars)]
                if j == 0:
                    couleur = (255, 230, 230, int(255 * k))
                else:
                    couleur = self.rouge + (int(230 * k * (1 - j / 16)),)
                d.text((x, y), car, font=self.f_code, fill=couleur, anchor="mm")

    def _griffes(self, d, dl, t, temps, k):
        u = self.u
        for j, (tg, pts) in enumerate(zip(temps, self.griffes)):
            age = t - tg
            if age < 0:
                continue
            f = lisse(age / 0.12)
            n = max(2, int(len(pts) * f))
            trace = pts[:n]
            frais = math.exp(-age / 0.35)
            a = k * (0.55 + 0.45 * frais)
            dl.line(trace, fill=self.rouge + (int(255 * a),), width=max(4, int((14 + 20 * frais) * u)), joint="curve")
            d.line(trace, fill=(255, 235 if frais > 0.3 else 60, 235 if frais > 0.3 else 70, int(255 * a)),
                   width=max(2, int((4 + 6 * frais) * u)), joint="curve")

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
