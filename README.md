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
Jacket_SACS — Generador de modelo SACS (.inp) desde CSV
=======================================================

Este proyecto contiene un script en Python (`build_sacs_inp.py`) que genera un archivo de entrada de SACS (`.inp`) a partir de CSV exportados de ETABS/SAP. Produce un modelo geométrico (sin cargas) y un listado de juntas en la línea de lodo (mudline) para fijarlas en SACS Precede.

Qué genera:
- `out/jacket_model.inp`: JOINT/SECT/GRUP/MEMBER en unidades SI (m, N, Pa)
- `out/mudline_joints.txt`: lista de joints con Z≈0 para asignar empotramientos

Requisitos
----------
- Linux (Debian/Ubuntu) o WSL2 en Windows
- Python 3.10 a 3.12
- Paquetes de Python listados en `requirements.txt`

Dependencias (requirements.txt)
-------------------------------
- pandas==2.2.2
- numpy==1.26.4
- openpyxl==3.1.5

Estructura del proyecto (sugerida)
----------------------------------
```
Jacket_SACS/
├─ build_sacs_inp.py     # script generador del .inp
├─ requirements.txt      # dependencias de Python
├─ run_build.sh          # script de conveniencia para ejecutar todo
├─ nodos.csv             # CSV de entrada (ver sección "Entradas")
├─ beam_conectivity.csv
├─ brace_conectivity.csv
├─ columns_conectivity.csv
├─ frame_assignments.csv
├─ secciones.csv
├─ material.csv          # opcional
└─ out/                  # salidas (se crea automáticamente)
```

Instalación y ejecución (Linux/WSL)
-----------------------------------

1) Instalar soporte para entornos virtuales (solo una vez):
```bash
sudo apt-get update
sudo apt-get install -y python3-venv
```

2) Preparar entorno, instalar dependencias y ejecutar con el script de conveniencia:
```bash
chmod +x run_build.sh
./run_build.sh
```

El script `run_build.sh` crea/activa el entorno virtual, instala dependencias (si hace falta) y ejecuta `build_sacs_inp.py` con rutas por defecto, escribiendo en `out/`.

Ejecución manual (alternativa)
------------------------------
```bash
# crear y activar venv
python3 -m venv venv
source venv/bin/activate

# instalar dependencias
python -m pip install --upgrade pip
pip install -r requirements.txt

# ejecutar usando los CSV en el directorio del repo
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
```

Entradas (CSV) y formato esperado
---------------------------------
- `nodos.csv`
  - Columnas: `UniqueName`, `X`, `Y`, `Z`.
  - Unidades: mm o m. El script detecta unidades y convierte a metros automáticamente. Puede ignorar una fila de unidades si existe.
- `beam_conectivity.csv`, `brace_conectivity.csv`, `columns_conectivity.csv`
  - Deben contener los IDs de nodo de los extremos I/J. El script detecta columnas tipo `UniquePtI`/`UniquePtJ` (tolerante a encabezados comunes de ETABS/SAP).
- `frame_assignments.csv`
  - Debe incluir una columna `Section Property` y una columna de identificador de frame (p. ej., `UniqueName`). Mapea cada frame a una sección.
- `secciones.csv`
  - Debe incluir `Name` (sección ETABS), `Outside Diameter` (mm), `Wall Thickness` (mm), `Material`. El script convierte OD y t a metros para SACS.
- `material.csv` (opcional)
  - Si se proporciona, puede incluir columnas para `E`, `nu`, `fy`, `rho`. Si faltan, se usan valores por defecto (A992Fy50): E=1.999e11 Pa, nu=0.30, fy=345 MPa, rho=7850 kg/m3.

Salidas
-------
- `out/jacket_model.inp`
  - Secciones: bloque `SECT` con tubos (OD, t en m)
  - Grupos: bloque `GRUP` con propiedades de material/sección
  - Nudos: bloque `JOINT` con coordenadas en m
  - Miembros: bloque `MEMBER` con pares I–J y grupo asociado
- `out/mudline_joints.txt`
  - Lista de joints con |Z| ≤ 0.001 m para empotrar (UX, UY, UZ, RX, RY, RZ) en Precede.

Uso de la CLI (argumentos)
--------------------------
```text
--nodes      ruta a nodos.csv                 (por defecto: nodos.csv)
--beams      ruta a beam_conectivity.csv      (por defecto: beam_conectivity.csv)
--braces     ruta a brace_conectivity.csv     (por defecto: brace_conectivity.csv)
--columns    ruta a columns_conectivity.csv   (por defecto: columns_conectivity.csv)
--assign     ruta a frame_assignments.csv     (por defecto: frame_assignments.csv)
--sections   ruta a secciones.csv             (por defecto: secciones.csv)
--material   ruta a material.csv              (por defecto: material.csv)
--out        archivo .inp de salida           (por defecto: jacket_model.inp)
--mudline    archivo de joints mudline        (por defecto: mudline_joints.txt)
```

Abrir en SACS (opcional)
------------------------
1) Precede (Modeler) → File → Open (o Import → SACS Input) → seleccionar `out/jacket_model.inp`
2) Unidades: Métrico (m, N, Pa)
3) Empotrar base: usar `out/mudline_joints.txt` para seleccionar joints con Z≈0 y fijar UX, UY, UZ, RX, RY, RZ

Solución de problemas
---------------------
- No se crea el venv: instala `python3-venv` (ver pasos de instalación)
- No aparecen barras (solo puntos): revisa que `frame_assignments.csv` contenga `Section Property` y que `secciones.csv` incluya todas las secciones usadas por los frames
- Diámetros/Espesores extraños: `secciones.csv` debe estar en mm; el script convierte a m
- CSV con separador `;`: vuelve a guardar como CSV con coma y codificación UTF-8
- Archivos abiertos en Excel: ciérralos antes de ejecutar

Integración con VS Code (opcional)
----------------------------------
Incluimos una tarea para ejecutar todo con un clic (Terminal → Run Task → "Run: build_sacs_inp")

Si deseas modificar rutas/argumentos, edita `.vscode/tasks.json`.

Notas
-----
- El script no coloca releases; todos los miembros son continuos.
- Los apoyos de base no se fijan en el `.inp` por compatibilidad; se listan en `mudline_joints.txt` para asignarlos en Precede.
