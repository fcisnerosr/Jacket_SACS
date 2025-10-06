README — Entorno WSL para ejecutar build_sacs_inp.py y generar el .inp de SACS
=============================================================================

Objetivo
--------
Correr el script en WSL (Ubuntu/Debian), producir `jacket_model.inp` y dejarlo en una
carpeta de Windows para abrirlo en SACS Precede.

0) Prerrequisitos
-----------------
- Windows 10/11 con WSL2 (Ubuntu recomendado).
- SACS instalado en Windows (para abrir el `.inp`).
- Permiso para escribir en C:\Users\<TU_USUARIO>\Desktop\… desde WSL.
- Python 3.10–3.12 dentro de WSL.


```python
1) Estructura de proyecto sugerida
----------------------------------
~/Jacket_SACS/
├─ data/                  # CSV de entrada (nodos, conectividad, secciones, etc.)
├─ out/                   # salidas (puedes redirigir a /mnt/c/... para Windows)
├─ venv/                  # entorno virtual de Python
├─ build_sacs_inp.py      # script generador del .inp
└─ requirements.txt
```

2) Instalar dependencias en WSL
-------------------------------
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

mkdir -p ~/Jacket_SACS/{data,out}
cd ~/Jacket_SACS
```

3) Crear requirements.txt
-------------------------
```bash
(cat > requirements.txt << 'EOF'
pandas==2.2.2
numpy==1.26.4
openpyxl==3.1.5
EOF
)
```
4) Crear y activar entorno virtual + instalar paquetes
------------------------------------------------------
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5) Colocar los archivos de entrada (en ~/Jacket_SACS/data/)
-----------------------------------------------------------
Nombres esperados:
- nodos.csv
- beam_conectivity.csv
- brace_conectivity.csv
- columns_conectivity.csv
- frame_assignments.csv
- secciones.csv
- material.csv  (opcional; si falta, usa A992Fy50 por defecto)

Ejemplo de copiado desde Windows:
```bash
cp /mnt/c/Users/<TU_USUARIO>/Downloads/nodos.csv               ~/Jacket_SACS/data/
cp /mnt/c/Users/<TU_USUARIO>/Downloads/beam_conectivity.csv    ~/Jacket_SACS/data/
cp /mnt/c/Users/<TU_USUARIO>/Downloads/brace_conectivity.csv   ~/Jacket_SACS/data/
cp /mnt/c/Users/<TU_USUARIO>/Downloads/columns_conectivity.csv ~/Jacket_SACS/data/
cp /mnt/c/Users/<TU_USUARIO>/Downloads/frame_assignments.csv   ~/Jacket_SACS/data/
cp /mnt/c/Users/<TU_USUARIO>/Downloads/secciones.csv           ~/Jacket_SACS/data/
# (opcional)
cp /mnt/c/Users/<TU_USUARIO>/Downloads/material.csv            ~/Jacket_SACS/data/
```

Notas de formato:
- nodos.csv: debe tener encabezados con UniqueName, X, Y, Z y (si existe) una fila de unidades en mm
  que el script sabe ignorar. Si ya está en metros y sin esa fila, también funcionará.
- secciones.csv: Outside Diameter y Wall Thickness en mm. El script convertirá a m en el .inp.
- CSV con separador coma (",") y UTF-8.

6) Colocar el script build_sacs_inp.py
--------------------------------------
Si ya lo tienes en Windows, cópialo:
cp /mnt/c/Users/<TU_USUARIO>/Downloads/build_sacs_inp.py ~/Jacket_SACS/
chmod +x ~/Jacket_SACS/build_sacs_inp.py

7) Ejecutar el script (salida hacia Windows)
--------------------------------------------
```bash
cd ~/Jacket_SACS
source venv/bin/activate
```

# Carpeta de salida en Windows (ajusta <TU_USUARIO>)
```bash
OUT_WIN="/mnt/c/Users/<TU_USUARIO>/Desktop/Jacket_SACS/out"
mkdir -p "$OUT_WIN"

python build_sacs_inp.py   --nodes    data/nodos.csv   --beams    data/beam_conectivity.csv   --braces   data/brace_conectivity.csv   --columns  data/columns_conectivity.csv   --assign   data/frame_assignments.csv   --sections data/secciones.csv   --material data/material.csv   --out      "$OUT_WIN/jacket_model.inp"   --mudline  "$OUT_WIN/mudline_joints.txt"
```

Salidas esperadas (en Windows):
C:\Users\<TU_USUARIO>\Desktop\Jacket_SACS\out\jacket_model.inp
C:\Users\<TU_USUARIO>\Desktop\Jacket_SACS\out\mudline_joints.txt

8) Abrir en SACS (desde Windows)
--------------------------------
1. SACS Executive → Precede (Modeler)
2. File → Open (o Import → SACS Input) → selecciona:
   C:\Users\<TU_USUARIO>\Desktop\Jacket_SACS\out\jacket_model.inp
3. Unidades: Métrico (m, N, Pa).
4. (Opcional) Empotrar base: selecciona joints con Z=0 (tolerancia ±0.001 m)
   → Joints → Restraints → fija UX, UY, UZ, RX, RY, RZ.

9) Script de conveniencia (run_build.sh)
----------------------------------------
Guárdalo en ~/Jacket_SACS/run_build.sh y hazlo ejecutable (chmod +x).
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
source venv/bin/activate
```

OUT_WIN="/mnt/c/Users/<TU_USUARIO>/Desktop/Jacket_SACS/out"
mkdir -p "$OUT_WIN"

python build_sacs_inp.py   --nodes    data/nodos.csv   --beams    data/beam_conectivity.csv   --braces   data/brace_conectivity.csv   --columns  data/columns_conectivity.csv   --assign   data/frame_assignments.csv   --sections data/secciones.csv   --material data/material.csv   --out      "$OUT_WIN/jacket_model.inp"   --mudline  "$OUT_WIN/mudline_joints.txt"

echo "Listo: $OUT_WIN/jacket_model.inp"

10) Verificaciones rápidas en WSL
---------------------------------
```bash
grep -cE '^JOINT  J'  "/mnt/c/Users/<TU_USUARIO>/Desktop/Jacket_SACS/out/jacket_model.inp"
grep -cE '^MEMBER'    "/mnt/c/Users/<TU_USUARIO>/Desktop/Jacket_SACS/out/jacket_model.inp"
grep -E  '^SECT|^GRUP' "/mnt/c/Users/<TU_USUARIO>/Desktop/Jacket_SACS/out/jacket_model.inp" | head -n 20
```

11) Problemas comunes
---------------------
- No veo barras (solo puntos): revisa que frame_assignments.csv y secciones.csv
  incluyan las secciones usadas por los frames (p. ej., SECC01, SECC04).
- Diámetros/Espesores raros: secciones.csv debe estar en mm; el script convierte a m.
- CSV con separador ';': vuelve a guardar como CSV con coma (UTF-8).
- Archivos abiertos en Excel: ciérralos antes de ejecutar el script.
- Permisos: si no puedes escribir en C:\..., verifica la ruta OUT_WIN o usa otra carpeta.

12) Versionado (.gitignore sugerido)
------------------------------------
/venv/
/out/*
*.log
*.lst
*.out
*.mdb
*.db
Thumbs.db
.DS_Store

Notas finales
-------------
- El script no coloca releases ni beta; todos los miembros son continuos.
- Los apoyos en mudline no se fijan en el .inp (varía por versión); se listan en mudline_joints.txt
  para asignarlos en Precede (empotrado 6 GDL).
