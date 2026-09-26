#!/usr/bin/env bash
# Sparse-clone only the CC0 recordings the score uses (~450 MB instead of several GB).
# Then: VSCO=... VCSL=... CC0SFX=... python3 compose.py ../score.wav
set -euo pipefail
DEST=${1:-"$(dirname "$0")/.samples"}; mkdir -p "$DEST"; cd "$DEST"
sparse() {  # repo dir pattern...
  local url=$1 dir=$2; shift 2
  [ -d "$dir" ] || GIT_LFS_SKIP_SMUDGE=1 git clone -q --depth 1 --filter=blob:none --no-checkout "$url" "$dir"
  git -C "$dir" sparse-checkout init --no-cone
  printf '%s\n' "$@" > "$dir/.git/info/sparse-checkout"
  git -C "$dir" checkout -q HEAD
}
sparse https://github.com/sgossner/VSCO-2-CE vsco \
  '/Strings/*/*' '/Brass/F Horn/*' '/Brass/Tenor Trombone/sus/*' '/Brass/Tuba/stac/*' '/Woodwinds/Flute/*' \
  '/Percussion/Glock/*' '/Percussion/Marimba/*' '/Percussion/Timpani/*' '/Percussion/BDrumNewhit_v6*' \
  '/Percussion/cymbal-crash*' '/Percussion/gongHit_fff.wav' '/Percussion/susCymb1-*' '/Percussion/Snare2-*' \
  '/Percussion/Triangle3-HitM_v1*' '/Percussion/Claves1_Hit_v2*' '/Miscellania Raw/Misc 1/glass_break*' \
  '/Miscellania Raw/Misc 2/glock_glisses/*' '/VSCO 1 Percussion/varWood/wood_click*'
sparse https://github.com/sgossner/VCSL vcsl \
  '/Idiophones/Friction Idiophones/Wine Glasses/*' '/Idiophones/Struck Idiophones/Hand Chimes/*' \
  '/Idiophones/Struck Idiophones/Claps/*' '/Idiophones/Struck Idiophones/Tubular Bells 1/*'
sparse https://github.com/lavenderdotpet/CC0-Public-Domain-Sounds cc0sfx \
  '/100-CC0-wood-metal-SFX/keys_*' '/kenney_uiaudio/*' '/kenney_casinoaudio/*' '/kenney_impactsounds/*' \
  '/kenney_interfacesounds/*' '/100-cc0-sfx-2/sfx100v2_stones_*' '/bb - Keyboard Sounds (Mar 2021)/*' \
  '/bb - Pill Bottles (Jun 2021)/*' "/bb - Rubik's Cube (Feb 2021)/*" '/bb - Bottle Plops (Apr 2021)/*'
echo "export VSCO=$PWD/vsco VCSL=$PWD/vcsl CC0SFX=$PWD/cc0sfx"
