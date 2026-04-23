"""
PDB file parser for the Gate & Channel framework.

Features:
  - Multi-model PDB (NMR): reads MODEL 1 only
  - Chain selection with fallback ('A', 'B', ' ')
  - Heavy atoms only (hydrogens excluded)
  - Returns backbone (dict), CA atoms (list), all_heavy (list)

Source: SSOC v3.32 (Iizumi 2026).
"""
import numpy as np
from ..physics.constants import THREE_TO_ONE


def parse_pdb(pdb_path, chain='A'):
    """Parse PDB file and extract backbone + CA atoms + all heavy atoms.

    Args:
        pdb_path: path to PDB file
        chain:    chain identifier (tries this first, then 'A', 'B', ' ')

    Returns:
        backbone:   dict {residue_num: {'rn': resname, 'N': xyz, 'CA': xyz, 'C': xyz}}
        atoms:      list [(residue_num, aa_letter, ca_xyz), ...]
        all_heavy:  list [(residue_num, atom_name, xyz), ...]
    """
    lines=open(pdb_path).read().split('\n')
    has_models=any(l.startswith('MODEL') for l in lines)
    filtered=[]
    in_model1=not has_models
    for l in lines:
        if l.startswith('MODEL'): in_model1=(int(l.split()[1])==1)
        if l.startswith('ENDMDL') and in_model1: filtered.append(l); break
        if in_model1: filtered.append(l)

    for ch_try in [chain,'A','B',' ']:
        backbone={};atoms=[];all_heavy=[]
        for l in filtered:
            if not l.startswith('ATOM'): continue
            an=l[12:16].strip();rn=l[17:20].strip();c=l[21]
            if c!=ch_try: continue
            if an.startswith('H'): continue
            try:
                rnum=int(l[22:26])
                xyz=np.array([float(l[30:38]),float(l[38:46]),float(l[46:54])])
            except: continue
            if an=='CA': atoms.append((rnum,THREE_TO_ONE.get(rn,'X'),xyz))
            if an in ('N','CA','C'):
                if rnum not in backbone: backbone[rnum]={'rn':rn}
                backbone[rnum][an]=xyz
            all_heavy.append((rnum,an,xyz))
        if len(atoms)>10: return backbone,atoms,all_heavy

    backbone={};atoms=[];all_heavy=[];seen=set()
    for l in filtered:
        if not l.startswith('ATOM'): continue
        an=l[12:16].strip();rn=l[17:20].strip()
        if an.startswith('H'): continue
        try:
            rnum=int(l[22:26])
            xyz=np.array([float(l[30:38]),float(l[38:46]),float(l[46:54])])
        except: continue
        if an=='CA' and rnum not in seen:
            atoms.append((rnum,THREE_TO_ONE.get(rn,'X'),xyz))
            seen.add(rnum)
        if an in ('N','CA','C'):
            if rnum not in backbone: backbone[rnum]={'rn':rn}
            if an not in backbone[rnum]: backbone[rnum][an]=xyz
        all_heavy.append((rnum,an,xyz))
    return backbone,atoms,all_heavy
