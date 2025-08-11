# -*- encoding: utf-8 -*-
import os
import json

import tempfile
import numpy as np
from pathlib import Path
from collections import defaultdict,OrderedDict
from rdkit import Chem
from rdkit.Chem import rdchem
from rdkit.Chem import AllChem,rdDetermineBonds


ELEMENT_FIX = {
    "CL": "Cl", "BR": "Br", "SI": "Si",
    "Xx": "H",
}

def safe_load_mol(mol_file):
    mol = Chem.MolFromMolFile(mol_file, sanitize=False, removeHs=False)
    return mol

def bond_order_mapper(temp, mol):
    if os.path.isfile(temp): 
        assert temp.endswith('.sdf')
        ref_mol = Chem.MolFromMolFile(temp, removeHs=True)
        Chem.SanitizeMol(ref_mol)
    else:
        # smiles
        params = Chem.SmilesParserParams()
        params.removeHs = True
        ref_mol = Chem.RemoveAllHs(Chem.MolFromSmiles(temp, params))
    
    Chem.Kekulize(ref_mol, clearAromaticFlags=True)

    try:
        prepared_ligand = assign_bond(ref_mol, mol)
    except:
        prepared_ligand = assign_bond2(ref_mol, mol)
    
    return prepared_ligand

def assign_bond(refmol, mol):
    refmol2 = Chem.Mol(refmol)
    mol2 = Chem.Mol(mol)  
    coords = np.array(mol2.GetConformer().GetPositions()).astype(np.float64)
    refmol3 = Chem.Mol(refmol)
    conf = mol2.GetConformer()
    try: # Assume that ref_mol and mol have exactly the same atom orders
        assert all([mol2.GetAtomWithIdx(i).GetSymbol() == refmol2.GetAtomWithIdx(i).GetSymbol() for i in range(refmol2.GetNumAtoms())]), 'Switch to substruct matching'
        conf.SetPositions(coords)
    except:
    # -Backup mapping strategy - to find matched substruct
    # Set bonds to SINGLE
        for b in mol2.GetBonds():
            if b.GetBondType() != Chem.BondType.SINGLE:
                b.SetBondType(Chem.BondType.SINGLE)
                b.SetIsAromatic(False)
        for b in refmol2.GetBonds():
            b.SetBondType(Chem.BondType.SINGLE)
            b.SetIsAromatic(False)
        # Set atom charges to zero;
        for a in refmol2.GetAtoms():
            a.SetFormalCharge(0)
        for a in mol2.GetAtoms():
            a.SetFormalCharge(0)
        matching = mol2.GetSubstructMatch(refmol2)
        conf.SetPositions(coords[list(matching),:])
    
    if refmol3.GetNumConformers() > 0:
        refmol3.RemoveAllConformers()
    refmol3.AddConformer(conf, assignId=True)
    
    Chem.SanitizeMol(refmol3)
    return refmol3

def assign_bond2(refmol, mol):
    newMol = AllChem.AssignBondOrdersFromTemplate(refmol, mol)
    Chem.SanitizeMol(newMol)
    return newMol


def save_mol(mol, output_sdf):
    Chem.MolToMolFile(mol, output_sdf)
    return None
