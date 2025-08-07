import pdb
import pickle
from os import remove
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from torchgen.api.structured import out_arguments

MD_DATA_DIR = "/hpc-cache-pfs/home/wtl/PDBbind_MD"


rdkit_mol_pkl = '/hpc-cache-pfs/home/dataland/af3-dev/release_data/components.v20240608.cif.rdkit_mol.pkl'
out_rdkit_mol_pkl = '/hpc-cache-pfs/home/dataland/af3-dev/release_data/components.v20250805.cif.rdkit_mol.pkl'
cluster_fn = '/hpc-cache-pfs/home/dataland/af3-dev/qiaojing/cluster_info.csv'


rdkit_mol_pkl = Path(rdkit_mol_pkl)
cluster_fn = Path(cluster_fn)
if rdkit_mol_pkl.exists():
    with open(rdkit_mol_pkl, "rb") as f:
        _ccd_rdkit_mols = pickle.load(f)

    print(f"{len(_ccd_rdkit_mols)=}")

if cluster_fn.exists():
    df = pd.read_csv(cluster_fn)
    print(f'{len(df)=}')
    df.drop_duplicates(subset=["name"], inplace=True)
    print(f'{len(df)=}')
    
    for _, row in df.iterrows():
        pdb_name = row["name"]
        lig_fn = Path(MD_DATA_DIR) / f"{pdb_name}_lig_opt/inputs/ligands/ligand.sdf"
        lig_mol: Chem.Mol = list(Chem.SDMolSupplier(lig_fn, removeHs=True))[0]
        lig_pdb_block = Chem.MolToPDBBlock(lig_mol)
        lig_pdb_mol = Chem.MolFromPDBBlock(lig_pdb_block, sanitize=False, proximityBonding=False)
        atom_map ={}
        ref_mask = []
        for atom in lig_pdb_mol.GetAtoms():
            atom: Chem.Atom
            pdb_info = atom.GetPDBResidueInfo()
            atom_map[pdb_info.GetName().strip()]=atom.GetIdx()
            ref_mask.append(True)
            

        lig_mol.atom_map=atom_map
        lig_mol.name = pdb_name
        lig_mol.sanitized = True
        lig_mol.ref_conf_id = 0
        lig_mol.ref_conf_type = 'rdkit'
        lig_mol.ref_mask = np.array(ref_mask)

        # if f"{pdb_name}c1" not in _ccd_rdkit_mols:
        #     for i in range(1,11):
        #         lig_name = f"{pdb_name}c{i}"
        _ccd_rdkit_mols[pdb_name]=lig_mol

    print(f"{len(_ccd_rdkit_mols)=}")

with open(out_rdkit_mol_pkl, "wb") as f:
    pickle.dump(_ccd_rdkit_mols, f)

print(out_rdkit_mol_pkl)

# rdkit_fn = # rdkit_fn = # rdkit_fn = # rdkit_fn = 