"""Crée une petite musique de démo (libre de droits, générée par code) pour tester le rendu.

    python demo_beat.py            → musique/demo.wav (20 s, 120 BPM)
"""

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 120
DUREE = 20.0


def enveloppe(n, decroissance):
    return np.exp(-np.arange(n) / (SR * decroissance))


def main():
    total = int(SR * DUREE)
    out = np.zeros(total)
    beat = 60 / BPM
    rng = np.random.default_rng(1)
    accords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (196.0, 246.9, 293.7), (164.8, 207.7, 246.9)]

    t_beat = 0.0
    k = 0
    while t_beat < DUREE:
        i = int(t_beat * SR)
        # Kick : sinus qui descend en fréquence
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        kick = np.sin(2 * np.pi * (45 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)) * enveloppe(n, 0.12)
        out[i:i + n] += kick[: total - i] * 0.9
        # Clap sur les temps 2 et 4
        if k % 2 == 1:
            n = int(0.2 * SR)
            clap = rng.normal(0, 1, n) * enveloppe(n, 0.04)
            out[i:i + n] += clap[: total - i] * 0.35
        # Charleston sur les croches
        j = int((t_beat + beat / 2) * SR)
        n = int(0.05 * SR)
        if j + n < total:
            out[j:j + n] += rng.normal(0, 1, n) * enveloppe(n, 0.01) * 0.15
        # Nappe d'accords qui change à chaque mesure (4 temps)
        if k % 4 == 0:
            n = int(beat * 4 * SR)
            tt = np.arange(n) / SR
            acc = accords[(k // 4) % len(accords)]
            nappe = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) for f in acc)
            env = np.minimum(1, tt * 8) * np.exp(-tt * 0.6)
            out[i:i + n] += (nappe * env)[: total - i] * 0.07
        t_beat += beat
        k += 1

    out /= np.max(np.abs(out)) * 1.1
    chemin = Path(__file__).resolve().parent / "musique" / "demo.wav"
    chemin.parent.mkdir(exist_ok=True)
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    print(f"✅ {chemin}")


if __name__ == "__main__":
    main()
