#!/usr/bin/env python3
"""Synthesize UI and motion-graphics sound effects locally. Seeded, so the same command gives the same file.

List recipes:     python3 sfx_synth.py --list
One sound:        python3 sfx_synth.py whoosh --out public/sfx/whoosh.wav [--length 0.6] [--pitch -3] [--seed 7]
Variations:       python3 sfx_synth.py click --variations 4 --out public/sfx/      (click-1.wav ... click-4.wav)
Typing burst:     python3 sfx_synth.py typing --count 18 --rate 14 --out public/sfx/typing.wav

Output: 48 kHz, 24-bit mono WAV, peak-normalized (default -1 dBFS). Pure Python standard library.
"""
import argparse
import math
import os
import random
import struct
import sys
import wave

SR = 48000
TAU = 2 * math.pi


def n(seconds):
    return max(1, int(seconds * SR))


# ---------- building blocks ----------

def silence(seconds):
    return [0.0] * n(seconds)


def mix_into(dst, src, at_s=0.0, gain=1.0):
    start = int(at_s * SR)
    need = start + len(src)
    if need > len(dst):
        dst.extend([0.0] * (need - len(dst)))
    for i, v in enumerate(src):
        dst[start + i] += v * gain
    return dst


def osc(freq_fn, seconds, shape="sine", phase=0.0):
    """freq_fn(t) -> Hz; supports sweeps. Shapes: sine, saw, square, triangle."""
    out, ph = [], phase
    for i in range(n(seconds)):
        t = i / SR
        ph = (ph + freq_fn(t) / SR) % 1.0
        if shape == "sine":
            v = math.sin(TAU * ph)
        elif shape == "saw":
            v = 2 * ph - 1
        elif shape == "square":
            v = 1.0 if ph < 0.5 else -1.0
        else:
            v = 4 * abs(ph - 0.5) - 1
        out.append(v)
    return out


def noise(seconds, rng, color="white"):
    out = []
    b0 = b1 = b2 = 0.0
    for _ in range(n(seconds)):
        w = rng.uniform(-1, 1)
        if color == "pink":  # Paul Kellet's economy pink filter
            b0 = 0.99765 * b0 + w * 0.0990460
            b1 = 0.96300 * b1 + w * 0.2965164
            b2 = 0.57000 * b2 + w * 1.0526913
            out.append((b0 + b1 + b2 + w * 0.1848) * 0.2)
        else:
            out.append(w)
    return out


def svf(sig, cutoff_fn, q=0.707, mode="low"):
    """Topology-preserving state-variable filter; stable with per-sample cutoff sweeps."""
    k = 1.0 / q
    ic1 = ic2 = 0.0
    out = []
    for i, v0 in enumerate(sig):
        fc = min(max(cutoff_fn(i / SR), 20.0), SR * 0.45)
        g = math.tan(math.pi * fc / SR)
        a1 = 1.0 / (1.0 + g * (g + k))
        a2 = g * a1
        a3 = g * a2
        v3 = v0 - ic2
        v1 = a1 * ic1 + a2 * v3
        v2 = ic2 + a2 * ic1 + a3 * v3
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        out.append(v2 if mode == "low" else v1 if mode == "band" else v0 - k * v1 - v2)
    return out


def const(x):
    return lambda t: x


def exp_sweep(f0, f1, seconds):
    return lambda t: f0 * (f1 / f0) ** min(1.0, t / seconds)


def env_decay(sig, decay_s, attack_s=0.0005):
    out = []
    L = len(sig)
    tail = min(n(0.003), L // 2)  # tiny end fade so layered pieces never click when they stop
    for i, v in enumerate(sig):
        t = i / SR
        a = min(1.0, t / attack_s) if attack_s > 0 else 1.0
        e = min(1.0, (L - i) / tail) if tail else 1.0
        out.append(v * a * e * math.exp(-t / decay_s))
    return out


def env_curve(sig, fn):
    """fn(x) for x in 0..1 across the signal."""
    L = len(sig)
    return [v * fn(i / L) for i, v in enumerate(sig)]


def bell(peak):
    """Rises to 1 at `peak` (0..1) and falls back, smooth at both ends."""
    def f(x):
        if x < peak:
            return math.sin(0.5 * math.pi * x / peak) ** 2
        return math.cos(0.5 * math.pi * (x - peak) / (1 - peak)) ** 2
    return f


def saturate(sig, drive=2.0):
    norm = math.tanh(drive)
    return [math.tanh(v * drive) / norm for v in sig]


def gain(sig, g):
    return [v * g for v in sig]


def add(*sigs):
    L = max(len(s) for s in sigs)
    out = [0.0] * L
    for s in sigs:
        for i, v in enumerate(s):
            out[i] += v
    return out


def space(sig, amount=0.2, delay_s=0.023, feedback=0.45):
    """A tiny feedback delay for a sense of room. amount 0 = dry."""
    if amount <= 0:
        return sig
    d = n(delay_s)
    out = sig + [0.0] * n(0.25)
    buf = [0.0] * len(out)
    for i in range(len(out)):
        echo = buf[i - d] if i >= d else 0.0
        buf[i] = out[i] + echo * feedback
        out[i] = out[i] + echo * amount
    return out


# ---------- recipes ----------
# Each takes (rng, length_scale, opts) and returns samples. Keep transients at the very start
# unless the sound has a natural build (whoosh, riser); sfx_analyze.py reports the peak offset.

def r_click(rng, L, o):
    body = env_decay(svf(noise(0.02 * L, rng), const(4200), q=1.5, mode="band"), 0.0025)
    tone = env_decay(osc(const(2200), 0.01 * L), 0.002)
    return add(body, gain(tone, 0.4))


def r_tick(rng, L, o):
    tone = env_decay(osc(exp_sweep(1900, 1500, 0.01), 0.045 * L), 0.006 * L)
    air = env_decay(svf(noise(0.004, rng), const(6000), mode="high"), 0.0008)
    return add(tone, gain(air, 0.5))


def r_pop(rng, L, o):
    tone = env_decay(osc(exp_sweep(950, 240, 0.04 * L), 0.16 * L), 0.022 * L, attack_s=0.001)
    snap = env_decay(svf(noise(0.006, rng), const(2500), mode="band"), 0.001)
    return add(tone, gain(snap, 0.35))


def r_tap(rng, L, o):
    tone = env_decay(osc(exp_sweep(700, 520, 0.02), 0.13 * L), 0.018 * L, attack_s=0.0015)
    thump = env_decay(svf(noise(0.06, rng), const(900)), 0.008)
    return add(tone, gain(thump, 0.6))


def r_whoosh(rng, L, o):
    d = 0.6 * L
    peak = 0.55
    cut = lambda t: 350 + 2600 * bell(peak)(min(1, t / d))
    body = svf(noise(d, rng, "pink"), cut, q=1.1, mode="band")
    return space(env_curve(body, bell(peak)), 0.12)


def r_swish(rng, L, o):
    d = 0.25 * L
    cut = lambda t: 1500 * (4.5 ** min(1, t / d))
    body = svf(noise(d, rng), cut, q=1.4, mode="band")
    return env_curve(body, bell(0.4))


def r_swipe(rng, L, o):
    d = 0.32 * L
    air = svf(noise(d, rng, "pink"), lambda t: 900 + 5000 * (t / d), q=1.0, mode="band")
    tone = gain(osc(exp_sweep(500, 1400, d), d), 0.08)
    return env_curve(add(air, tone), bell(0.35))


def r_riser(rng, L, o):
    d = 1.6 * L
    air = svf(noise(d, rng, "pink"), exp_sweep(200, 7000, d), q=2.0, mode="band")
    tone = gain(svf(osc(exp_sweep(110, 880, d), d, "saw"), exp_sweep(400, 5000, d)), 0.25)
    return env_curve(add(air, tone), lambda x: x ** 2.2)


def r_downer(rng, L, o):
    d = 1.0 * L
    air = svf(noise(d, rng, "pink"), exp_sweep(6000, 180, d), q=1.6, mode="band")
    tone = gain(osc(exp_sweep(700, 60, d), d, "triangle"), 0.35)
    return env_curve(add(air, tone), lambda x: (1 - x) ** 1.5 * min(1, x * 40))


def r_impact(rng, L, o):
    d = 1.8 * L
    sub = env_decay(osc(exp_sweep(130, 42, 0.09), d), 0.28 * L, attack_s=0.0008)
    crack = env_decay(svf(noise(0.4, rng), exp_sweep(2500, 250, 0.2)), 0.07)
    body = saturate(add(sub, gain(crack, 0.7)), 1.8)
    return space(body, 0.18, delay_s=0.041, feedback=0.4)


def r_hit(rng, L, o):
    d = 0.5 * L
    kick = env_decay(osc(exp_sweep(220, 70, 0.05), d), 0.08 * L, attack_s=0.0005)
    snap = env_decay(svf(noise(0.15, rng), const(1800), q=0.9, mode="band"), 0.035)
    return saturate(add(kick, gain(snap, 0.8)), 2.2)


def r_glitch(rng, L, o):
    out = []
    t = 0.0
    while t < 0.35 * L:
        seg = rng.uniform(0.008, 0.04)
        if rng.random() < 0.3:
            piece = silence(seg)
        elif rng.random() < 0.5:
            piece = gain(osc(const(rng.choice([180, 320, 640, 1250, 2400])), seg, "square"), 0.5)
        else:
            step = rng.choice([4, 8, 16])
            raw = noise(seg, rng)
            piece = [raw[i - i % step] * 0.7 for i in range(len(raw))]  # sample-and-hold crunch
        out.extend(piece)
        t += seg
    return out


def _bell_tone(f, d, partials=((1, 1.0, 1.0), (2.76, 0.5, 0.45), (5.4, 0.25, 0.25), (8.93, 0.12, 0.15))):
    out = silence(d)
    for ratio, amp, dec in partials:
        mix_into(out, env_decay(osc(const(f * ratio), d), d * 0.15 * dec, attack_s=0.001), 0, amp)
    return out


def r_ding(rng, L, o):
    return space(_bell_tone(1320, 1.4 * L), 0.15)


def r_chime(rng, L, o):  # success / complete
    out = silence(1.4 * L)
    mix_into(out, _bell_tone(1318.5, 1.1 * L), 0.0, 0.8)
    mix_into(out, _bell_tone(1975.5, 1.2 * L), 0.09, 0.7)
    return space(out, 0.15)


def r_notify(rng, L, o):
    out = silence(0.75 * L)
    for at, f in ((0.0, 880), (0.13 * L, 1320)):
        mix_into(out, env_decay(osc(const(f), 0.6 * L), 0.09 * L, attack_s=0.004), at, 0.8)
    return out


def r_error(rng, L, o):
    out = silence(0.35 * L)
    for at in (0.0, 0.16 * L):
        buzz = svf(osc(const(160), 0.12 * L, "square"), const(1400))
        mix_into(out, env_curve(buzz, lambda x: min(1, x * 30) * (1 - x) ** 0.5), at, 0.6)
    return out


def r_beep(rng, L, o):
    return env_curve(osc(const(1000), 0.09 * L), lambda x: min(1, x * 20) * min(1, (1 - x) * 10))


def r_sparkle(rng, L, o):
    d = 0.9 * L
    out = silence(d + 0.3)
    for i in range(14):
        at = d * 0.75 * (i / 14) ** 1.6
        f = rng.uniform(3000, 8000)
        blip = env_decay(osc(const(f), 0.28), rng.uniform(0.015, 0.04), attack_s=0.0008)
        mix_into(out, blip, at, rng.uniform(0.25, 0.6) * (1 - i / 20))
    return space(out, 0.25, delay_s=0.031)


def r_shutter(rng, L, o):
    out = silence(0.16 * L)
    for at, f in ((0.0, 3500), (0.065 * L, 2600)):
        mix_into(out, env_decay(svf(noise(0.03, rng), const(f), q=1.2, mode="band"), 0.006), at, 1.0)
    return out


def r_typing(rng, L, o):
    count, rate = o.count, o.rate
    out = silence(count / rate + 0.1)
    t = 0.0
    for _ in range(count):
        sub = random.Random(rng.random())
        f = sub.uniform(2600, 4200)
        key = add(env_decay(svf(noise(0.03, sub), const(f), q=1.3, mode="band"), sub.uniform(0.003, 0.007)),
                  gain(env_decay(svf(noise(0.06, sub), const(500)), 0.01), 0.5))
        mix_into(out, key, t, sub.uniform(0.55, 1.0))
        t += (1 / rate) * sub.uniform(0.6, 1.4)
    return out


RECIPES = {
    "click": (r_click, "very short UI click; buttons, toggles, cursor"),
    "tick": (r_tick, "tiny tonal tick; counters, list items, small text"),
    "pop": (r_pop, "bubbly pop; icons and shapes appearing"),
    "tap": (r_tap, "soft rounded tap; cards landing, gentle UI"),
    "whoosh": (r_whoosh, "air movement peaking mid-sound; objects passing, transitions"),
    "swish": (r_swish, "fast bright swish; quick slides, text sweeping in"),
    "swipe": (r_swipe, "screen swipe; carousel, page change"),
    "riser": (r_riser, "build-up that ends on the hit; reveals (place its end on the reveal frame)"),
    "downer": (r_downer, "falling sweep; exits, drop-offs"),
    "impact": (r_impact, "deep cinematic hit with tail; logo lands, big reveals"),
    "hit": (r_hit, "short punchy hit; bold text slams, beat accents"),
    "glitch": (r_glitch, "digital stutter; tech transitions, errors"),
    "ding": (r_ding, "single bell; highlights, achievements"),
    "chime": (r_chime, "two-note success chime; completion, checkmarks"),
    "notify": (r_notify, "two-tone notification; messages, alerts"),
    "error": (r_error, "double buzz; wrong answer, failed state"),
    "beep": (r_beep, "plain sine beep; timers, scanners"),
    "sparkle": (r_sparkle, "glittering high blips; magic, shine, premium moments"),
    "shutter": (r_shutter, "camera shutter; screenshots, photo moments"),
    "typing": (r_typing, "keyboard typing burst; text typing on (use --count/--rate)"),
}


# ---------- output ----------

def finish(sig, pitch, peak_db):
    if pitch:
        ratio = 2 ** (pitch / 12)
        L = int(len(sig) / ratio)
        sig = [sig[min(int(i * ratio), len(sig) - 1)] * (1 - (i * ratio) % 1) +
               sig[min(int(i * ratio) + 1, len(sig) - 1)] * ((i * ratio) % 1) for i in range(L)]
    # Trim trailing near-silence, then short fades so files never start or end with a click.
    peak = max((abs(v) for v in sig), default=0.0) or 1.0
    floor = peak * 10 ** (-60 / 20)
    end = len(sig)
    while end > 1 and abs(sig[end - 1]) < floor:
        end -= 1
    sig = sig[: min(len(sig), end + n(0.01))]
    # Fade-out: 10% of the sound, 4-60 ms, so an unfinished decay never ends in a click.
    fi, fo = n(0.0003), min(max(n(0.004), len(sig) // 10), n(0.06), len(sig) // 2)
    for i in range(min(fi, len(sig))):
        sig[i] *= i / fi
    for i in range(fo):
        sig[-1 - i] *= i / fo
    target = 10 ** (peak_db / 20)
    peak = max(abs(v) for v in sig) or 1.0
    return [v * target / peak for v in sig]


def write_wav(path, sig):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    frames = bytearray()
    for v in sig:
        iv = max(-8388608, min(8388607, int(round(v * 8388607))))
        frames += struct.pack("<i", iv)[:3]
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(bytes(frames))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("recipe", nargs="?", choices=sorted(RECIPES))
    p.add_argument("--out", help="output .wav, or a directory (file named after the recipe)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--variations", type=int, default=1, help="write N files with consecutive seeds")
    p.add_argument("--pitch", type=float, default=0.0, help="semitones (also changes length)")
    p.add_argument("--length", type=float, default=1.0, help="length multiplier (0.5 = twice as short)")
    p.add_argument("--peak-db", type=float, default=-1.0)
    p.add_argument("--count", type=int, default=16, help="typing: number of keystrokes")
    p.add_argument("--rate", type=float, default=12.0, help="typing: keystrokes per second")
    a = p.parse_args()

    if a.list or not a.recipe:
        for name in sorted(RECIPES):
            print(f"  {name:<8} {RECIPES[name][1]}")
        return
    if not a.out:
        p.error("--out is required")
    if not (0.1 <= a.length <= 5) or a.variations < 1 or a.count < 1 or a.rate <= 0:
        p.error("length must be 0.1-5, variations/count >= 1, rate > 0")

    fn = RECIPES[a.recipe][0]
    is_dir = a.out.endswith(os.sep) or os.path.isdir(a.out) or a.variations > 1
    for k in range(a.variations):
        seed = a.seed + k
        sig = finish(fn(random.Random(seed), a.length, a), a.pitch, a.peak_db)
        if is_dir:
            suffix = f"-{k + 1}" if a.variations > 1 else ""
            path = os.path.join(a.out, f"{a.recipe}{suffix}.wav")
        else:
            path = a.out
        write_wav(path, sig)
        print(f"Wrote {path}  ({len(sig) / SR:.3f}s, seed {seed}, pitch {a.pitch:+g} st)")


if __name__ == "__main__":
    sys.exit(main())
