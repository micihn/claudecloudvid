"""PORTOKO — 20 s orchestral score built only from real recordings (all CC0).

Tempo 120 BPM (one 16th = 0.125 s, one bar = 2 s). Every cut in the film lands on the grid:
  0.0  intro: office chaos (typing, switches, dice) + glass rub + timpani roll
  2.0  TUTTI hit (glass break, gong, timpani, horns) -> groove + the hook
  4.0  "UN" slam            5.0-7.5 one object accent per word (configure/build/connect/...)
  8.0  portal -> orbit: strings, harp, flute, wine glasses, chimes (half-time)
 11.5  flow build: spiccato ostinato, snare + timpani rolls, rising strings
 14.0  drop: hook on horns + strings + glock, full object percussion
 17.5  end card: C major resolve, tubular bell, final switch "click"
Usage: python3 compose.py out.wav   (sample roots via VSCO / VCSL / CC0SFX env vars)
"""
import os, sys
import numpy as np
from sampler import SR, Inst, Hit, Bus, hall, load

HERE = os.path.dirname(os.path.abspath(__file__))
V = os.environ.get('VSCO', os.path.join(HERE, '.samples', 'vsco'))
C = os.environ.get('VCSL', os.path.join(HERE, '.samples', 'vcsl'))
X = os.environ.get('CC0SFX', os.path.join(HERE, '.samples', 'cc0sfx'))
DUR = 20.0
S16 = 0.125
rng = np.random.default_rng(12)
hum = lambda s=0.006: rng.uniform(-s, s)          # human timing
hv = lambda v, s=0.08: v * rng.uniform(1 - s, 1 + s)  # human velocity

# ------------------------------------------------------------------ instruments
vln_pizz = Inst(f'{V}/Strings/Violin Section/Pizz/*.wav', 0.55, 12)
vln_spic = Inst(f'{V}/Strings/Violin Section/Spic/*.wav', 0.5, 12)
vln_sus = Inst(f'{V}/Strings/Violin Section/susVib/*.wav', 0.42, 12)
vla_sus = Inst(f'{V}/Strings/Viola Section/susvib/*.wav', 0.38, 12)
cel_sus = Inst(f'{V}/Strings/Cello Section/susvib/*.wav', 0.45, 12)
cel_spic = Inst(f'{V}/Strings/Cello Section/spic/*.wav', 0.5, 12)
cel_pizz = Inst(f'{V}/Strings/Cello Section/pizzT/*.wav', 0.5, 12)
cb_pizz = Inst(f'{V}/Strings/Solo Contrabass/Pizz/*.wav', 0.75, 12)
harp = Inst(f'{V}/Strings/Harp/*.wav', 0.5, 0)
horn = Inst(f'{V}/Brass/F Horn/sus/*.wav', 0.5, 12)
horn_st = Inst(f'{V}/Brass/F Horn/stac/*.wav', 0.5, 12)
tbn = Inst(f'{V}/Brass/Tenor Trombone/sus/*.wav', 0.45, 12)
tuba = Inst(f'{V}/Brass/Tuba/stac/*.wav', 0.6, 12)
flute = Inst(f'{V}/Woodwinds/Flute/susvib/*.wav', 0.4, 12)
flute_st = Inst(f'{V}/Woodwinds/Flute/stac/*.wav', 0.35, 12)
glock = Inst(f'{V}/Percussion/Glock/*.wav', 0.32, 0)
marimba = Inst(f'{V}/Percussion/Marimba/*.wav', 0.45, 12)
tubular = Inst(f'{C}/Idiophones/Struck Idiophones/Tubular Bells 1/*_ff_*.wav', 0.4, 0)
chimes = Inst(f'{C}/Idiophones/Struck Idiophones/Hand Chimes/*.wav', 0.35, 0)
wine = Inst(f'{C}/Idiophones/Friction Idiophones/Wine Glasses/Sustains/Slow/*.wav', 0.5, 0)

timp = Hit(f'{V}/Percussion/Timpani/Timpani[1-5]_Hit_v3_rr1*.wav', 0.9)
timp_roll = Hit(f'{V}/Percussion/Timpani/Rolls/*_v5_*.wav', 0.6)
bdrum = Hit(f'{V}/Percussion/BDrumNewhit_v6*.wav', 0.9)
crash = Hit(f'{V}/Percussion/cymbal-crash1_ff_rr1.wav', 0.55)
crash_s = Hit(f'{V}/Percussion/cymbal-crashshort*.wav', 0.45)
gong = Hit(f'{V}/Percussion/gongHit_fff.wav', 0.6)
cym_cresc = Hit(f'{V}/Percussion/susCymb1-cresc-Median*.wav', 0.5)
cym_cresc_l = Hit(f'{V}/Percussion/susCymb1-cresc-Long*.wav', 0.5)
cym_bow = Hit(f'{V}/Percussion/susCymb1-bow-1.wav', 0.3)
snare_roll = Hit(f'{V}/Percussion/Snare2-rollNS_v5*.wav', 0.4)
snare = Hit(f'{V}/Percussion/Snare2-HitNS_v3*.wav', 0.35)
triangle = Hit(f'{V}/Percussion/Triangle3-HitM_v1*.wav', 0.22)
claves = Hit(f'{V}/Percussion/Claves1_Hit_v2*.wav', 0.3)
wood = Hit(f'{V}/VSCO 1 Percussion/varWood/wood_click*.wav', 0.35, 0.25)
glass_break = Hit(f'{V}/Miscellania Raw/Misc 1/glass_break[2-4].wav', 0.45)
glock_up = Hit(f'{V}/Miscellania Raw/Misc 2/glock_glisses/glock_fx_up_chromatic_fast*.wav', 0.35)
claps = Hit(f'{C}/Idiophones/Struck Idiophones/Claps/Clap_rr*.wav', 0.35, 0.3)

# small objects
keys = Hit(f'{X}/100-CC0-wood-metal-SFX/keys_*.ogg', 0.4)
switch = Hit(f'{X}/kenney_uiaudio/Audio/switch*.ogg', 0.3, 0.12)
modeld = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Model D - Switch *.wav', 0.35, 0.2)
typing = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Keyboard - Typing 1.wav', 0.35)
keytap = Hit(f'{X}/bb - Keyboard Sounds (Mar 2021)/Keyboard - Key [0-9].wav', 0.35, 0.15)
glass_tap = Hit(f'{X}/kenney_impactsounds/Audio/impactGlass_light_*.ogg', 0.35)
glass_ui = Hit(f'{X}/kenney_interfacesounds/Audio/glass_*.ogg', 0.3)
chips = Hit(f'{X}/kenney_casinoaudio/Audio/chipsCollide*.ogg', 0.35)
dice = Hit(f'{X}/kenney_casinoaudio/Audio/diceThrow*.ogg', 0.35)
stones = Hit(f'{X}/100-cc0-sfx-2/sfx100v2_stones_*.ogg', 0.3)
pills = Hit(f'{X}/bb - Pill Bottles (Jun 2021)/*Roll*.wav', 0.3)
rubik = Hit(f'{X}/bb - Rubik\'s Cube (Feb 2021)/Small Cube - Twist *.wav', 0.4, 0.3)
plop = Hit(f'{X}/bb - Bottle Plops (Apr 2021)/Plop - Airy *.wav', 0.4)

# ------------------------------------------------------------------ harmony + hook
# chord name -> (bass root, pad voicing)
CH = {
    'Am': (33, [45, 57, 60, 64, 69]), 'F': (29, [41, 57, 60, 65, 69]), 'C': (36, [48, 55, 60, 64, 67]),
    'G': (31, [43, 55, 59, 62, 67]), 'Dm': (38, [50, 57, 62, 65, 69]), 'E': (28, [40, 56, 59, 64, 68]),
    'Fmaj7': (29, [41, 57, 60, 64, 69]), 'Cmaj7': (36, [48, 55, 59, 64, 71]),
}
# the hook: a 3-3-2 syncopated figure, one per chord (16th steps within a bar)
HOOK = {
    'Am': {0: 81, 3: 76, 6: 81, 8: 79, 10: 76, 12: 74, 14: 76},
    'F': {0: 77, 3: 72, 6: 77, 8: 76, 10: 72, 12: 69, 14: 72},
    'C': {0: 79, 3: 76, 6: 79, 8: 76, 10: 72, 12: 74, 14: 76},
    'G': {0: 79, 3: 74, 6: 79, 8: 77, 10: 74, 12: 71, 14: 74},
}


def hook(inst, t0, chord, steps=16, trans=0, gain=1.0, pan=0.0, legato=1.0, dur_cap=None):
    h = HOOK[chord]; ks = sorted(k for k in h if k < steps)
    for i, k in enumerate(ks):
        nxt = ks[i + 1] if i + 1 < len(ks) else steps
        d = (nxt - k) * S16 * legato
        if dur_cap: d = min(d, dur_cap)
        acc = 1.0 if k in (0, 6) else 0.85
        bus.add(inst.note(h[k] + trans, d, hv(acc)), t0 + k * S16 + hum(), gain, pan)


def bass(t0, chord, steps=16, gain=1.0, inst=None):
    r = CH[chord][0]
    for k, o in ((0, 0), (3, 0), (6, 12), (8, 0), (11, 7), (14, 12)):
        if k >= steps: break
        bus.add((inst or cb_pizz).note(r + o, 0.3, hv(1.0 if k in (0, 8) else 0.8)), t0 + k * S16 + hum(0.004), gain)


def pad(t0, chord, dur, gain=1.0, top=True):
    v = CH[chord][1]
    bus.add(cel_sus.note(v[0], dur, 1.0, 0.5), t0 + hum(), gain, -0.3)
    bus.add(vla_sus.note(v[1], dur, 0.9, 0.5), t0 + hum(), gain, 0.2)
    bus.add(vla_sus.note(v[2], dur, 0.8, 0.5), t0 + hum(), gain, 0.3)
    bus.add(vln_sus.note(v[3], dur, 0.8, 0.5), t0 + hum(), gain, -0.2)
    if top: bus.add(vln_sus.note(v[4], dur, 0.7, 0.5), t0 + hum(), gain, 0.4)


def swell_into(hit, t, gain):  # reversed recording that ends exactly on t
    bus.add(hit.get(1.0, rev=True), t, gain, 0, end_at=True)


bus = Bus(DUR)
_place = bus.add
def _add_with_outro(sig, t, gain=1.0, pan=0.0, end_at=False):
    # the end card resolves softer than the drop
    _place(sig, t, gain * (0.72 if t >= 17.5 and not end_at else 1.0), pan, end_at)
bus.add = _add_with_outro

# ================================================================== 0-2  what's tangled
bus.add(typing.get(1.0, dur=1.85), 0.05, 0.75, -0.35)
for k in range(16):
    t = k * S16
    if k % 2 == 0: bus.add(switch.get(hv(1)), t + hum(0.01), 0.8 if k % 4 == 0 else 0.5, 0.5)
    if rng.random() < 0.25 + k * 0.03: bus.add(keytap.get(hv(0.8)), t + 0.06 + hum(0.02), 0.6, rng.uniform(-.7, .7))
bus.add(dice.get(), 0.62, 0.55, 0.6)
bus.add(chips.get(), 1.18, 0.5, -0.6)
bus.add(wine.note(69, 2.2, 1.0, 0.3), 0.0, 0.5, -0.2)
bus.add(wine.note(76, 2.0, 0.8, 0.3), 0.3, 0.35, 0.3)
for k, s in enumerate((0, 3, 6)):  # the hook, foreshadowed
    bus.add(glock.note(HOOK['Am'][s], 0.4, 0.7), 1.0 + s * S16, 0.9, 0.2)
roll = timp_roll.get(1.0, k=0, dur=1.0); roll = roll * np.linspace(0.05, 1, len(roll))[:, None] ** 2
bus.add(roll, 1.0, 0.9)
swell_into(crash, 2.0, 0.55)
bus.add(keys.get(k=2), 1.25, 0.45, -0.4)

# ================================================================== 2.0 tutti hit
bus.add(bdrum.get(), 2.0, 1.0)
bus.add(timp.get(k=0), 2.0, 0.9)
bus.add(gong.get(), 2.0, 0.55)
bus.add(crash.get(), 2.0, 0.6)
bus.add(glass_break.get(k=0), 2.0, 0.5, 0.3)
for n in (45, 52, 57): bus.add(horn.note(n, 1.3, 1.0, 0.6), 2.0, 0.8)
bus.add(tbn.note(45, 1.2, 1.0, 0.6), 2.0, 0.7)
pad(2.0, 'Am', 1.6, 0.9)

# ================================================================== 2-8 groove + hook
def groove(t0, bars, dens=1.0, backbeat=True):
    for b in range(bars):
        tb = t0 + b * 2.0
        for k in range(16):
            t = tb + k * S16
            if k in (0, 8): bus.add(bdrum.get(hv(0.7)), t, 0.6)
            if k in (6, 14) and dens > 0.6: bus.add(bdrum.get(hv(0.4)), t, 0.35)
            if backbeat and k in (4, 12):
                bus.add(claps.get(hv(1)), t + hum(0.004), 0.8, 0.1); bus.add(wood.get(hv(1)), t, 0.6, -0.2)
            if k % 2 == 0 or dens > 1.2:  # switch "hats"
                bus.add(switch.get(hv(1)), t + hum(0.003), (0.55 if k % 4 == 2 else 0.35) * min(1.2, dens), 0.45)
            if k in (2, 6, 10, 14): bus.add(keys.get(hv(1), dur=0.22), t + 0.01, 0.35 * dens, -0.5)
            if rng.random() < 0.12 * dens: bus.add(stones.get(hv(1), dur=0.25), t + hum(0.02), 0.35, rng.uniform(-.8, .8))

groove(2.0, 3, 0.9, backbeat=False)
for t0, ch, st in ((2.0, 'Am', 16), (4.0, 'F', 16), (6.0, 'C', 8), (7.0, 'G', 8)):
    hook(vln_pizz, t0, ch, st, 0, 0.9, -0.25, 0.9, 0.35)
    hook(glock, t0, ch, st, 12 if t0 >= 4 else 0, 0.55, 0.35, 1, 0.5)
    if t0 >= 4: hook(marimba, t0, ch, st, -12, 0.45, 0.1, 1, 0.4)
    bass(t0, ch, st, 0.8)
    pad(t0, ch, st * S16, 0.32 if t0 > 2 else 0.0, top=False)
# 3.0 onward: backbeat claps
for tb in (3.0,):
    pass
for t in np.arange(3.0, 7.75, 1.0):
    bus.add(claps.get(hv(1)), t + 0.5 + hum(0.004), 0.75, 0.1); bus.add(wood.get(hv(1)), t + 0.5, 0.55, -0.2)

# 4.0 "UN" slam
bus.add(timp.get(k=2), 4.0, 0.9); bus.add(crash_s.get(), 4.0, 0.5); bus.add(claves.get(), 3.93, 0.6, -0.6)
for n in (53, 57, 60): bus.add(horn_st.note(n, 0.3, 1.0), 4.0, 0.8)
bus.add(glock_up.get(), 4.45, 0.55, 0.3)
swell_into(crash_s, 5.0, 0.5)

# 5.0-7.5 one object accent per word
bus.add(modeld.get(k=0), 5.0, 0.8, -0.3); bus.add(modeld.get(k=3), 5.06, 0.6, 0.3); bus.add(switch.get(k=5), 5.12, 0.6)   # CONFIGURE
bus.add(rubik.get(k=0), 5.5, 0.8, 0.2); bus.add(snare.get(), 5.5, 0.5)                                                 # BUILD
bus.add(glass_tap.get(k=1), 6.0, 0.8, -0.2); bus.add(glass_ui.get(k=2), 6.02, 0.5, 0.4)                                # CONNECT
bus.add(chimes.note(84, 1.0, 1.0), 6.5, 0.6, 0.3); bus.add(harp.note(81, 0.8), 6.5, 0.6, -0.3)                         # REDESIGN
bus.add(dice.get(k=1), 7.0, 0.6, -0.3); bus.add(snare.get(), 7.0, 0.4)                                                 # PROCESS
bus.add(plop.get(k=0), 7.25, 0.8, 0.3)                                                                                 # FLOW
bus.add(wine.note(81, 0.6, 1.0, 0.3), 7.5, 0.6); bus.add(glass_tap.get(k=3), 7.5, 0.5)                                 # ODOO
for i, n in enumerate((69, 72, 76, 79, 81, 84)): bus.add(harp.note(n, 0.6), 7.5 + i * 0.04, 0.5, -0.5 + i * 0.2)
sr = snare_roll.get(1.0, dur=0.5); sr = sr * np.linspace(0.1, 1, len(sr))[:, None]
bus.add(sr, 7.5, 0.6)
swell_into(crash, 8.0, 0.6)

# ================================================================== 8-11.5 orbit (half-time, wonder)
bus.add(gong.get(), 8.0, 0.5); bus.add(timp.get(k=3), 8.0, 0.8); bus.add(bdrum.get(), 8.0, 0.8)
bus.add(glock_up.get(k=1), 8.0, 0.4, 0.4)
pad(8.0, 'Fmaj7', 2.1, 0.75); pad(10.0, 'Cmaj7', 1.6, 0.75)
bus.add(cb_pizz.note(29, 0.8), 8.0, 0.7); bus.add(cb_pizz.note(36, 0.8), 10.0, 0.7)
for i, n in enumerate([53, 57, 60, 64, 65, 69, 72, 76] * 2):           # harp arpeggios
    bus.add(harp.note(n + (0 if i < 8 else -5), 0.9, hv(0.8)), 8.0 + i * 0.25 + hum(), 0.55, -0.5 + (i % 8) * 0.14)
for i, n in enumerate([81, 79, 76, 77]):                               # hook, slowed on flute
    bus.add(flute.note(n, 0.7 if i < 3 else 1.2, 0.9, 0.25), 8.5 + i * 0.75, 0.75, 0.2)
for t in (8.25, 9.1, 9.6, 10.35, 10.8):
    bus.add(glass_tap.get(hv(0.7)), t, 0.35, rng.uniform(-.8, .8))
bus.add(chimes.note(88, 1.5, 0.8), 9.0, 0.4, -0.5); bus.add(chimes.note(84, 1.5, 0.8), 10.0, 0.4, 0.5)
bus.add(wine.note(76, 2.5, 0.7, 0.4), 8.4, 0.35, 0.5)
bus.add(cym_bow.get(), 8.6, 0.6, -0.3)
bus.add(pills.get(k=0, dur=1.6), 9.0, 0.35, 0.6)
bus.add(timp.get(k=4), 9.0, 0.35); bus.add(timp.get(k=4), 10.0, 0.35)
# dive
bus.add(cym_cresc.get(), 11.5, 0.7, 0, end_at=True)
r2 = timp_roll.get(1.0, k=1, dur=0.9); r2 = r2 * np.linspace(0.05, 1, len(r2))[:, None] ** 2
bus.add(r2, 10.6, 0.8)
bus.add(keys.get(k=0), 11.0, 0.5, 0.4)

# ================================================================== 11.5-14 flow: the build
bus.add(bdrum.get(), 11.5, 0.8); bus.add(timp.get(k=1), 11.5, 0.7)
for t0, ch in ((11.5, 'C'), (12.0, 'Dm'), (12.5, 'Dm'), (13.0, 'E'), (13.5, 'E')):
    r = CH[ch][0] + 12
    for k in range(4):   # 16th spiccato ostinato
        bus.add(cel_spic.note(r + (12 if k == 2 else 0), 0.14, hv(1.0 if k == 0 else 0.7)), t0 + k * S16 + hum(0.003), 0.8, -0.3)
    bus.add(cb_pizz.note(CH[ch][0], 0.3), t0, 0.6)
pad(11.5, 'C', 0.5, 0.4); pad(12.0, 'Dm', 1.0, 0.5); pad(13.0, 'E', 1.0, 0.6)
for k in range(20):
    t = 11.5 + k * S16
    bus.add(switch.get(hv(1)), t, 0.35 + 0.02 * k, 0.45)
    if k % 4 == 0 and t >= 12.0: bus.add(bdrum.get(hv(0.7)), t, 0.55)
bus.add(typing.get(1.0, dur=1.2), 11.6, 0.35, -0.4)
for k, t in enumerate(np.arange(12.0, 14.0, 0.25)):   # marbles (dice + chips) accelerating
    bus.add((chips if k % 2 else stones).get(hv(1), dur=0.3), t + hum(0.01), 0.3 + k * 0.02, rng.uniform(-.7, .7))
sr = snare_roll.get(1.0, dur=1.5); sr = sr * np.linspace(0.05, 1, len(sr))[:, None] ** 1.5
bus.add(sr, 12.5, 0.75)
r3 = timp_roll.get(1.0, k=2, dur=1.0); r3 = r3 * np.linspace(0.1, 1, len(r3))[:, None] ** 2
bus.add(r3, 13.0, 0.8)
for i, n in enumerate((64, 65, 68, 69, 71, 72, 74, 76)):   # E harmonic minor run into the drop
    bus.add(vln_spic.note(n + 12, 0.14, hv(0.7 + i * 0.04)), 13.0 + i * S16, 0.8, 0.3)
    bus.add(flute_st.note(n + 12, 0.12, 0.8), 13.0 + i * S16, 0.45, -0.2)
bus.add(cym_cresc_l.get(), 14.0, 0.5, 0, end_at=True)
swell_into(crash, 14.0, 0.5)

# ================================================================== 14-17.5 the drop
bus.add(bdrum.get(), 14.0, 1.0); bus.add(timp.get(k=0), 14.0, 1.0); bus.add(gong.get(), 14.0, 0.55)
bus.add(crash.get(), 14.0, 0.65); bus.add(glass_ui.get(k=0), 14.0, 0.5, 0.5)
groove(14.0, 2, 1.25)
for t0, ch, st in ((14.0, 'Am', 16), (16.0, 'F', 8), (17.0, 'G', 4)):
    hook(horn, t0, ch, st, -12, 0.9, -0.2, 0.95)
    hook(vln_spic, t0, ch, st, 0, 0.75, 0.3, 0.9, 0.3)
    hook(glock, t0, ch, st, 12, 0.45, 0.4, 1, 0.5)
    hook(flute_st, t0, ch, st, 0, 0.4, -0.4, 1, 0.2)
    bass(t0, ch, st, 0.8); bass(t0, ch, st, 0.6, tuba)
    pad(t0, ch, st * S16, 0.45)
    for k in range(0, st, 4): bus.add(triangle.get(hv(1)), t0 + (k + 2) * S16, 0.6, 0.6)
bus.add(glock_up.get(k=2), 17.0, 0.5, 0.3)
sr = snare_roll.get(1.0, dur=0.5); sr = sr * np.linspace(0.1, 1, len(sr))[:, None]
bus.add(sr, 17.0, 0.7)
swell_into(crash, 17.5, 0.6)

# ================================================================== 17.5 end card: resolve to C major
bus.add(bdrum.get(), 17.5, 0.9); bus.add(timp.get(k=1), 17.5, 0.9); bus.add(crash.get(), 17.5, 0.5)
bus.add(gong.get(), 17.5, 0.35)
for n in (48, 55, 60, 64): bus.add(horn.note(n, 1.8, 0.9, 1.2), 17.5, 0.75)
bus.add(tbn.note(36, 1.8, 0.9, 1.2), 17.5, 0.6)
pad(17.5, 'C', 1.9, 0.8)
bus.add(cb_pizz.note(24 + 12, 0.8), 17.5, 0.8)
for i, n in enumerate((60, 64, 67, 72, 76, 79, 84)):
    bus.add(harp.note(n, 1.5, hv(0.9)), 17.5 + i * 0.05, 0.6, -0.6 + i * 0.2)
bus.add(tubular.note(60, 2.5, 1.0), 17.5, 0.55)
bus.add(glock.note(84, 1.5, 0.8), 17.5, 0.5)
bus.add(wine.note(79, 2.4, 0.9, 0.4), 17.6, 0.4, 0.3)
bus.add(chimes.note(84, 1.5, 0.7), 18.2, 0.3, -0.4)
# the final click: job done
bus.add(modeld.get(k=1), 19.05, 0.9); bus.add(glass_tap.get(k=0), 19.07, 0.55, 0.2)

# ================================================================== mix
dry = bus.x
wet = hall(dry, rt=2.4)
mix = dry * 0.85 + wet * 0.42
# gentle glue: soft-knee limiter to -1 dBFS
peak = np.abs(mix).max(); mix = mix / peak * 1.25
mix = np.tanh(mix) / np.tanh(1.25) * 0.89
t = np.arange(len(mix)) / SR
mix *= np.minimum(1, (DUR - t) / 0.3)[:, None]
import soundfile as sf
out = sys.argv[1] if len(sys.argv) > 1 else 'score.wav'
sf.write(out, mix.astype(np.float32), SR, subtype='PCM_24')
print('wrote', out)
