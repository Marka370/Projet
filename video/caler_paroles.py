"""Cale des paroles (fichier texte, une ligne = une phrase) sur une transcription
automatique horodatée mot par mot, et produit la liste « paroles » du script vidéo.

La transcription (format transformers.js / Whisper : {"chunks": [{"text", "timestamp"}]})
contient souvent des fautes, surtout sur du rap. On aligne donc les deux suites de mots
(alignement global type Needleman-Wunsch avec similarité floue entre mots) : les mots
bien reconnus servent d'ancres, les autres sont interpolés entre deux ancres.

    python caler_paroles.py musique/bang_x_capuche_paroles.txt musique/bang_x_capuche_mots.json \\
        --debut 27 --fin 65.3 > paroles.json

Les lignes entre parenthèses (chœurs) sont ignorées ; --chœurs pour les garder.
Avec --debut, les temps sont donnés depuis --debut (comme dans le script vidéo).
"""

import argparse
import difflib
import json
import re
import sys
import unicodedata

import numpy as np


def normaliser(mot):
    mot = unicodedata.normalize("NFD", mot.lower())
    mot = "".join(c for c in mot if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", mot)


def jetons(texte):
    """Découpe en jetons comparables : « j'descends » → « j », « descends »."""
    return [j for j in (normaliser(x) for x in re.split(r"[\s'’\-]+", texte)) if j]


def similarite(a, b, cache={}):
    cle = (a, b)
    if cle not in cache:
        cache[cle] = difflib.SequenceMatcher(None, a, b).ratio()
    return cache[cle]


def aligner(a, b, trou=-0.45):
    """Alignement global ; renvoie {indice dans a: indice dans b} pour les paires similaires."""
    n, m = len(a), len(b)
    score = np.zeros((n + 1, m + 1), np.float32)
    score[:, 0] = np.arange(n + 1) * trou
    score[0, :] = np.arange(m + 1) * trou
    choix = np.zeros((n + 1, m + 1), np.uint8)  # 0 diag, 1 haut, 2 gauche
    for i in range(1, n + 1):
        ai = a[i - 1]
        for j in range(1, m + 1):
            d = score[i - 1, j - 1] + 2 * similarite(ai, b[j - 1]) - 1
            h = score[i - 1, j] + trou
            g = score[i, j - 1] + trou
            if d >= h and d >= g:
                score[i, j], choix[i, j] = d, 0
            elif h >= g:
                score[i, j], choix[i, j] = h, 1
            else:
                score[i, j], choix[i, j] = g, 2
    paires = {}
    i, j = n, m
    while i > 0 and j > 0:
        c = choix[i, j]
        if c == 0:
            if similarite(a[i - 1], b[j - 1]) >= 0.5:
                paires[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif c == 1:
            i -= 1
        else:
            j -= 1
    return paires


def charger_transcription(chemin, decalage=0.0):
    with open(chemin, encoding="utf-8") as f:
        data = json.load(f)
    mots = []
    for c in data["chunks"]:
        t0, t1 = c["timestamp"]
        for k, j in enumerate(jetons(c["text"])):
            mots.append((j, t0 + decalage, (t1 if t1 is not None else t0) + decalage))
    return mots


def caler(lignes, transcription):
    # jetons des paroles, avec (ligne, mot affiché) d'origine
    toks, origine = [], []
    for li, ligne in enumerate(lignes):
        for mi, mot in enumerate(ligne.split()):
            for j in jetons(mot):
                toks.append(j)
                origine.append((li, mi))
    paires = aligner(toks, [m[0] for m in transcription])

    # temps de chaque jeton : ancre si alignée, sinon interpolation
    temps = np.full(len(toks), np.nan)
    for i, j in paires.items():
        temps[i] = transcription[j][1]
    connus = np.where(~np.isnan(temps))[0]
    if len(connus) < 2:
        sys.exit("Trop peu de mots reconnus pour caler les paroles.")
    ancres = temps.copy()
    temps = np.interp(np.arange(len(toks)), connus, temps[connus])
    # un mot non reconnu juste avant une ancre est chanté juste avant elle,
    # pas au milieu du silence qui précède
    for k in range(len(toks)):
        if np.isnan(ancres[k]):
            suiv = connus[connus > k]
            if len(suiv):
                temps[k] = max(temps[k], ancres[suiv[0]] - 0.28 * (suiv[0] - k))
    temps = np.maximum.accumulate(temps)  # les paroles avancent toujours dans le temps
    fin_mot = {i: transcription[j][2] for i, j in paires.items()}

    resultat = []
    for li, ligne in enumerate(lignes):
        idx = [k for k, o in enumerate(origine) if o[0] == li]
        if not idx:
            continue
        mots_t = {}
        for k in idx:
            mots_t.setdefault(origine[k][1], temps[k])
        fiables = sum(1 for k in idx if k in paires) / len(idx)
        fin = max(fin_mot.get(idx[-1], temps[idx[-1]] + 0.5), temps[idx[-1]] + 0.35)
        resultat.append({
            "debut": float(temps[idx[0]]),
            "fin": float(fin),
            "texte": ligne,
            "mots": [round(float(mots_t[k]), 2) for k in sorted(mots_t)],
            "fiabilite": round(fiables, 2),
        })
    # monotonie des temps, et une ligne ne déborde pas sur la suivante
    for r in resultat:
        r["mots"] = [float(x) for x in np.maximum.accumulate(r["mots"])]
        r["debut"] = r["mots"][0]
        r["fin"] = max(r["fin"] + 0.4, r["mots"][-1] + 0.3)
    for a, b in zip(resultat, resultat[1:]):
        a["fin"] = min(a["fin"], b["debut"] - 0.05)
    for r in resultat:
        r["fin"] = round(r["fin"], 2)
    return resultat


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paroles")
    ap.add_argument("transcription")
    ap.add_argument("--decalage", type=float, default=0.0, help="décalage à ajouter aux temps de la transcription")
    ap.add_argument("--debut", type=float, default=0.0)
    ap.add_argument("--fin", type=float, default=None)
    ap.add_argument("--choeurs", action="store_true", help="garder les lignes entre parenthèses")
    args = ap.parse_args()

    with open(args.paroles, encoding="utf-8") as f:
        lignes = [l.strip() for l in f if l.strip()]
    if not args.choeurs:
        lignes = [l for l in lignes if not (l.startswith("(") and l.endswith(")"))]

    res = caler(lignes, charger_transcription(args.transcription, args.decalage))
    fin = args.fin if args.fin is not None else float("inf")
    sortie = []
    for r in res:
        if r["debut"] >= args.debut and r["debut"] < fin:
            d = args.debut
            sortie.append({"debut": round(r["debut"] - d, 2), "fin": round(min(r["fin"], fin) - d, 2),
                           "texte": r["texte"], "mots": [round(x - d, 2) for x in r["mots"]]})
            print(f"{r['debut']:7.2f}  ({r['fiabilite']:.0%})  {r['texte']}", file=sys.stderr)
    json.dump(sortie, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
