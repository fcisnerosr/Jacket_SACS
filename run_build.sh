#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Activate venv if exists; else create it and install deps
if [[ -d venv ]]; then
  source venv/bin/activate
else
  python3 -m venv venv
  source venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
fi

mkdir -p out

python build_sacs_inp.py \
  --nodes    nodos.csv \
  --beams    beam_conectivity.csv \
  --braces   brace_conectivity.csv \
  --columns  columns_conectivity.csv \
  --assign   frame_assignments.csv \
  --sections secciones.csv \
  --material material.csv \
  --out      out/jacket_model.inp \
  --mudline  out/mudline_joints.txt

echo "Listo: out/jacket_model.inp"