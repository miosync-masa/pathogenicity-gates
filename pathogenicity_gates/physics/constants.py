"""
Physical constants and amino acid property tables.

Source: SSOC v3.32 (Iizumi 2026, under review at Acta Materialia).

References:
  - AA_HYDRO:          Kyte-Doolittle hydropathy scale (1982)
  - AA_VOLUME:         Zamyatnin volumes (1972, A^3)
  - AA_CHARGE:         Formal charge at pH 7
  - AA_HBDON/HBACC:    H-bond donor/acceptor count (sidechain)
  - AA_AROMATIC:       Aromatic ring indicator
  - AA_SULFUR:         Sulfur-containing residue indicator
  - HELIX_PROP:        Chou-Fasman alpha-helix propensity (SSOC-calibrated)
  - BETA_PROP:         Chou-Fasman beta-strand propensity (SSOC-calibrated)
  - C_CAVITY:          Cavity formation energy coefficient (SSOC v3.12)
  - C_HYDRO_TRANSFER:  Hydrophobic transfer energy coefficient (SSOC v3.12)

These are the 13 "constant atoms" of the Gate & Channel framework.
"""

AA_HYDRO = {
    'I': 4.5, 'V': 4.2, 'L': 3.8, 'F': 2.8, 'C': 2.5, 'M': 1.9, 'A': 1.8,
    'G': -0.4, 'T': -0.7, 'S': -0.8, 'W': -0.9, 'Y': -1.3, 'P': -1.6,
    'H': -3.2, 'D': -3.5, 'E': -3.5, 'N': -3.5, 'Q': -3.5, 'K': -3.9, 'R': -4.5
}

AA_VOLUME = {
    'G': 60.1, 'A': 88.6, 'V': 140.0, 'L': 166.7, 'I': 166.7, 'P': 112.7,
    'F': 189.9, 'W': 227.8, 'Y': 193.6, 'M': 162.9, 'C': 108.5, 'S': 89.0,
    'T': 116.1, 'N': 114.1, 'D': 111.1, 'Q': 143.8, 'E': 138.4, 'H': 153.2,
    'K': 168.6, 'R': 173.4
}

AA_CHARGE = {'D': -1.0, 'E': -1.0, 'K': 1.0, 'R': 1.0, 'H': 0.1}
AA_AROMATIC = {'F': 1.0, 'W': 1.0, 'Y': 1.0, 'H': 0.5}
AA_SULFUR = {'C': 1.0, 'M': 1.0}
AA_HBDON = {'S': 1, 'T': 1, 'N': 1, 'Q': 1, 'Y': 1, 'W': 1, 'H': 1, 'K': 1, 'R': 2, 'C': 0.5}
AA_HBACC = {'S': 1, 'T': 1, 'N': 1, 'Q': 1, 'Y': 1, 'D': 2, 'E': 2, 'H': 1}

POLAR_SET = set('STNQDEHKR')
CHARGE_AA = {'D', 'E', 'K', 'R', 'H'}

HELIX_PROP = {
    'A': 1.0, 'L': 0.79, 'M': 0.74, 'E': 0.71, 'K': 0.65, 'Q': 0.61,
    'R': 0.56, 'I': 0.52, 'F': 0.47, 'D': 0.40, 'W': 0.37, 'V': 0.35,
    'T': 0.31, 'S': 0.29, 'N': 0.28, 'H': 0.27, 'Y': 0.25, 'C': 0.24,
    'G': 0.00, 'P': -0.50,
}

BETA_PROP = {
    'V': 1.0, 'I': 0.95, 'T': 0.75, 'F': 0.70, 'Y': 0.70, 'W': 0.65,
    'L': 0.55, 'C': 0.50, 'M': 0.45, 'A': 0.30, 'R': 0.25, 'K': 0.20,
    'Q': 0.15, 'E': 0.10, 'S': 0.10, 'H': 0.10, 'D': 0.05, 'N': 0.05,
    'G': 0.00, 'P': -0.30,
}

C_CAVITY = 0.075
C_HYDRO_TRANSFER = 0.055

THREE_TO_ONE = {
    'ALA': 'A', 'CYS': 'C', 'ASP': 'D', 'GLU': 'E', 'PHE': 'F', 'GLY': 'G',
    'HIS': 'H', 'ILE': 'I', 'LYS': 'K', 'LEU': 'L', 'MET': 'M', 'ASN': 'N',
    'PRO': 'P', 'GLN': 'Q', 'ARG': 'R', 'SER': 'S', 'THR': 'T', 'VAL': 'V',
    'TRP': 'W', 'TYR': 'Y'
}
