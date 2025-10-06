#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera un archivo SACS .inp (geométrico, sin cargas) desde CSV exportados de ETABS/SAP:
- nodos.csv (UniqueName, X, Y, Z en mm o m)
- beam_conectivity.csv, brace_conectivity.csv, columns_conectivity.csv (UniquePtI/UniquePtJ)
- frame_assignments.csv (Frame UniqueName ↔ Section Property)
- secciones.csv (Name, Outside Diameter (mm), Wall Thickness (mm), Material)
- material.csv (opcional: E, nu, fy, rho) — si no está, usa A992Fy50 por defecto
Crea también mudline_joints.txt con los joints a empotrar (Z≈0).
"""

import pandas as pd
import numpy as np
import argparse
import os, sys

def read_nodes(path):
    raw = pd.read_csv(path, header=None, encoding='utf-8-sig')
    # localizar fila de encabezados
    hdr = None
    for i in range(min(6, len(raw))):
        row = raw.iloc[i].astype(str).str.lower().tolist()
        if any('uniquename' in x for x in row) and any(x.strip()=='x' for x in row):
            hdr = i; break
    if hdr is None: hdr = 1
    df = pd.read_csv(path, header=hdr, encoding='utf-8-sig')
    # quitar fila de unidades
    if 'X' not in df.columns:
        raise RuntimeError("nodos.csv: no encuentro columna 'X'. Revisa el archivo.")
    df = df[~df['X'].astype(str).str.contains('mm', na=False)].copy()
    df['UniqueName'] = pd.to_numeric(df['UniqueName'], errors='coerce').astype('Int64')
    # detectar unidad: si valores grandes (>>100), probablemente mm
    X = pd.to_numeric(df['X'], errors='coerce')
    unit_factor = 1.0/1000.0 if (X.dropna().abs().median()>50) else 1.0
    df['x_m'] = pd.to_numeric(df['X'], errors='coerce')*unit_factor
    df['y_m'] = pd.to_numeric(df['Y'], errors='coerce')*unit_factor
    df['z_m'] = pd.to_numeric(df['Z'], errors='coerce')*unit_factor
    df = df.dropna(subset=['UniqueName','x_m','y_m','z_m'])[['UniqueName','x_m','y_m','z_m']].reset_index(drop=True)
    return df

def read_conn(path):
    df = pd.read_csv(path)
    df2 = df.iloc[1:].copy()
    c_frame = df.columns[0]
    c_I, c_J = None, None
    for c in df.columns:
        cl = c.lower()
        if 'uniquep' in cl and 'i' in cl and c_I is None: c_I = c
        if 'uniquep' in cl and 'j' in cl and c_J is None: c_J = c
    if c_I is None: c_I = df.columns[3]
    if c_J is None: c_J = df.columns[4]
    df2 = df2.rename(columns={c_frame:'frame_id', c_I:'UniquePtI', c_J:'UniquePtJ'})
    for c in ['frame_id','UniquePtI','UniquePtJ']:
        df2[c] = pd.to_numeric(df2[c], errors='coerce').astype('Int64')
    df2 = df2.dropna(subset=['frame_id','UniquePtI','UniquePtJ'])
    return df2[['frame_id','UniquePtI','UniquePtJ']]

def read_frame_assign(path):
    raw = pd.read_csv(path, header=None)
    hdr = None
    for i in range(min(12, len(raw))):
        row = raw.iloc[i].astype(str).tolist()
        if any('Section Property' in x for x in row):
            hdr = i; break
    if hdr is None: hdr = 1
    df = raw.copy()
    df.columns = raw.iloc[hdr].tolist()
    df = df.iloc[hdr+1:].copy()
    # detectar columna id y seccion
    cand_id = [c for c in df.columns if str(c).lower().strip() in ['uniquename','frame name','frame','id','unique name']]
    id_col = cand_id[0] if cand_id else df.columns[0]
    if 'Section Property' not in df.columns:
        raise RuntimeError("frame_assignments.csv: no encuentro 'Section Property'.")
    out = df[[id_col, 'Section Property']].rename(columns={id_col:'frame_id', 'Section Property':'etabs_section'}).copy()
    out['frame_id'] = pd.to_numeric(out['frame_id'], errors='coerce').astype('Int64')
    out = out.dropna(subset=['frame_id','etabs_section'])
    return out

def read_sections(path):
    raw = pd.read_csv(path, header=None)
    hdr = None
    for i in range(min(12, len(raw))):
        row = raw.iloc[i].astype(str).tolist()
        if ('Name' in row) and ('Outside Diameter' in row):
            hdr = i; break
    if hdr is None: hdr = 0
    df = raw.copy()
    df.columns = raw.iloc[hdr].tolist()
    df = df.iloc[hdr+2:].copy()  # salta fila de unidades
    df = df.rename(columns={'Name':'etabs_section','Outside Diameter':'OD_mm','Wall Thickness':'t_mm','Material':'material'})
    df['OD_mm'] = pd.to_numeric(df['OD_mm'], errors='coerce')
    df['t_mm']  = pd.to_numeric(df['t_mm'], errors='coerce')
    df = df.dropna(subset=['etabs_section','OD_mm','t_mm'])[['etabs_section','OD_mm','t_mm','material']].copy()
    return df

def read_material(path):
    # Espera columnas E, nu, fy, rho (o equivalentes). Si falla, devuelve A992Fy50.
    try:
        df = pd.read_csv(path)
        cols = [c.lower().strip() for c in df.columns]
        # heurística ligera
        def pick(name, alts):
            for c in df.columns:
                if c.lower().strip() in [name]+alts:
                    return float(df[c].iloc[0])
            return None
        E  = pick('e',  ['e1','young','modulus'])
        nu = pick('nu', ['poisson','v','nu12'])
        fy = pick('fy', ['yield','fy_mpa'])
        rho= pick('rho',['density','densidad','rho_kgm3'])
        # Defaults A992Fy50 si falta algo
        if E is None:  E  = 1.9994798e11
        if nu is None: nu = 0.30
        if fy is None: fy = 345e6
        if rho is None:rho= 7850.0
        return E, nu, fy, rho
    except Exception:
        return 1.9994798e11, 0.30, 345e6, 7850.0

def jid(n):
    try: return f"J{int(n)}"
    except: return f"J{str(n).strip()}"

def main(args):
    nodes = read_nodes(args.nodes)
    beams  = read_conn(args.beams)
    braces = read_conn(args.braces)
    cols   = read_conn(args.columns)
    frames_conn = pd.concat([beams.assign(tipo='beam'),
                             braces.assign(tipo='brace'),
                             cols.assign(tipo='column')], ignore_index=True)
    fa_map = read_frame_assign(args.assign)
    secs   = read_sections(args.sections)
    # usar solo secciones que aparecen en frames
    used_secs = set(fa_map['etabs_section'].unique())
    secs = secs[secs['etabs_section'].isin(used_secs)].copy()
    E, nu, fy, rho = read_material(args.material) if args.material else (1.9994798e11, 0.30, 345e6, 7850.0)

    sections_map = secs.copy()
    sections_map['sacs_section_name'] = sections_map['etabs_section']
    sections_map['sacs_group'] = sections_map['etabs_section'] + "_GRP"
    sections_map['E'] = E; sections_map['nu']=nu; sections_map['fy']=fy; sections_map['rho']=rho
    sections_map['OD_m'] = sections_map['OD_mm'] / 1000.0
    sections_map['t_m']  = sections_map['t_mm']  / 1000.0

    members = frames_conn.merge(fa_map, on='frame_id', how='left') \
                         .merge(sections_map[['etabs_section','sacs_group']], on='etabs_section', how='left')
    if members['sacs_group'].isna().any():
        missing = int(members['sacs_group'].isna().sum())
        raise RuntimeError(f"{missing} miembros sin grupo mapeado: revisa 'frame_assignments' y 'secciones'.")

    # —— generar .inp ——
    tol_z = 0.001
    mudline_ids = [jid(i) for i in nodes.loc[nodes['z_m'].abs() <= tol_z, 'UniqueName']]
    L = []
    L.append("* ============================================================")
    L.append("* Modelo geométrico SACS — generado desde CSV (SI: m, N, Pa)")
    L.append("* JOINT/SECT/GRUP/MEMBER — sin releases; empotramientos ver listado")
    L.append("* ============================================================")
    L.append("OPTIONS  MN")
    L.append("")
    L.append("* --- SECCIONES TUBULARES ---")
    L.append("SECT")
    for _,r in sections_map.iterrows():
        L.append(f"SECT  {r['sacs_section_name']:<12s}  TUB  {r['OD_m']:.6f}  {r['t_m']:.6f}")
    L.append("")
    L.append("* --- GRUPOS (Material/Sección) ---")
    L.append("GRUP")
    for _,r in sections_map.iterrows():
        L.append(f"GRUP  {r['sacs_group']:<12s}  {r['sacs_section_name']:<12s}  {r['E']:.6E}  {r['nu']:.2f}  {r['fy']:.6E}  {r['rho']:.1f}")
    L.append("")
    L.append("* --- JOINTS (id  X  Y  Z) ---")
    L.append("JOINT")
    for _,r in nodes.iterrows():
        L.append(f"JOINT  {jid(r['UniqueName']):<12s}  {r['x_m']:.3f}  {r['y_m']:.3f}  {r['z_m']:.3f}")
    L.append("")
    L.append("* --- MEMBERS (A  B  Grupo) ---")
    L.append("MEMBER")
    for _,r in members.iterrows():
        L.append(f"MEMBER  {jid(r['UniquePtI']):<12s}  {jid(r['UniquePtJ']):<12s}  {r['sacs_group']}")
    L.append("END")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    with open(args.mudline, "w", encoding="utf-8") as f:
        f.write("* Joints a empotrar (Z≈0) — fijar UX,UY,UZ,RX,RY,RZ\n")
        for j in mudline_ids: f.write(j+"\n")

    print(f"OK: escrito {args.out}")
    print(f"OK: escrito {args.mudline}")
    print(f"Secciones usadas: {sorted(list(used_secs))}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--nodes",   default="nodos.csv")
    ap.add_argument("--beams",   default="beam_conectivity.csv")
    ap.add_argument("--braces",  default="brace_conectivity.csv")
    ap.add_argument("--columns", default="columns_conectivity.csv")
    ap.add_argument("--assign",  default="frame_assignments.csv")
    ap.add_argument("--sections",default="secciones.csv")
    ap.add_argument("--material",default="material.csv")
    ap.add_argument("--out",     default="jacket_model.inp")
    ap.add_argument("--mudline", default="mudline_joints.txt")
    args = ap.parse_args()
    main(args)
