"""Génère une voix off française à partir d'un texte (synthèse vocale locale, gratuite).

Utilise les voix libres Piper via sherpa-onnx (pip install sherpa-onnx). Les voix sont
téléchargées automatiquement depuis les « releases » GitHub de sherpa-onnx.

Entrée : un JSON [{ "id", "texte" (affiché), "dit" (prononcé, optionnel) }, ...]
Sortie : un .wav complet + un JSON de chronologie (début / fin de chaque phrase,
         temps estimé de chaque mot) prêt pour l'animation.

    python voix_off.py ninja_legacy/voix_off.json --voix tom --vitesse 0.95
"""

import argparse
import json
import re
import subprocess
import tarfile
import urllib.request
import wave
from pathlib import Path

import numpy as np

DOSSIER = Path(__file__).resolve().parent
VOIX = {
    "tom": "fr_FR-tom-medium",       # voix masculine
    "siwis": "fr_FR-siwis-medium",   # voix féminine
    "gilles": "fr_FR-gilles-low",
}
URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-{}.tar.bz2"


def modele(nom, cache):
    dossier = cache / f"vits-piper-{nom}"
    if not dossier.exists():
        cache.mkdir(parents=True, exist_ok=True)
        archive = cache / f"{nom}.tar.bz2"
        print(f"Téléchargement de la voix {nom}…")
        urllib.request.urlretrieve(URL.format(nom), archive)
        with tarfile.open(archive) as t:
            t.extractall(cache, filter="data")
        archive.unlink()
    return dossier


def moteur(dossier, nom):
    import sherpa_onnx
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(dossier / f"{nom}.onnx"), tokens=str(dossier / "tokens.txt"),
            data_dir=str(dossier / "espeak-ng-data")),
        num_threads=4))
    return sherpa_onnx.OfflineTts(cfg)


def rogner(x, sr, seuil=0.01):
    """Enlève le silence au début et à la fin d'une phrase."""
    actif = np.where(np.abs(x) > seuil)[0]
    if not len(actif):
        return x
    a = max(0, actif[0] - int(0.03 * sr))
    b = min(len(x), actif[-1] + int(0.08 * sr))
    return x[a:b]


def temps_des_mots(texte, debut, fin):
    """Répartit les mots sur la durée de la phrase, au prorata de leur longueur
    (+ une petite pause après la ponctuation)."""
    mots = texte.split()
    poids = []
    for m in mots:
        p = len(re.sub(r"\W", "", m)) + 2
        if re.search(r"[,;:.!?…]$", m):
            p += 4
        poids.append(p)
    total = sum(poids)
    t, res = debut, []
    for p in poids:
        res.append(round(t, 3))
        t += (fin - debut) * p / total
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script")
    ap.add_argument("--voix", default="tom", choices=sorted(VOIX))
    ap.add_argument("--vitesse", type=float, default=1.0)
    ap.add_argument("--pause", type=float, default=0.45, help="silence entre deux phrases (s)")
    ap.add_argument("--debut", type=float, default=1.2, help="silence avant la première phrase (s)")
    ap.add_argument("--cache", default=str(Path.home() / ".cache" / "voix_piper"))
    args = ap.parse_args()

    script = Path(args.script)
    lignes = json.loads(script.read_text(encoding="utf-8"))
    nom = VOIX[args.voix]
    tts = moteur(modele(nom, Path(args.cache)), nom)

    morceaux, chrono, t = [], [], args.debut
    sr = None
    for l in lignes:
        a = tts.generate(l.get("dit") or l["texte"], sid=0, speed=args.vitesse)
        sr = a.sample_rate
        x = rogner(np.array(a.samples, dtype=np.float32), sr)
        if not morceaux:
            morceaux.append(np.zeros(int(args.debut * sr), np.float32))
        morceaux.append(x)
        d = len(x) / sr
        chrono.append({"id": l["id"], "texte": l["texte"], "debut": round(t, 3), "fin": round(t + d, 3),
                       "mots": temps_des_mots(l["texte"], t, t + d)})
        pause = float(l.get("pause_apres", args.pause))
        morceaux.append(np.zeros(int(pause * sr), np.float32))
        t += d + pause
        print(f"{chrono[-1]['debut']:6.2f}–{chrono[-1]['fin']:6.2f}  {l['texte']}")

    audio = np.concatenate(morceaux)
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.9
    sortie = script.with_name(script.stem + f"_{args.voix}.wav")
    with wave.open(str(sortie), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((audio * 32767).astype(np.int16).tobytes())
    script.with_name(script.stem + f"_{args.voix}_chrono.json").write_text(
        json.dumps({"audio": sortie.name, "duree": round(len(audio) / sr, 3), "phrases": chrono},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ {sortie} ({len(audio) / sr:.1f} s)")


if __name__ == "__main__":
    main()
