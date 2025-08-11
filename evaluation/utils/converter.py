# -*- encoding: utf-8 -*-
import os
import json

from rdkit import Chem
from rdkit.Chem import rdDetermineBonds
from biotite.structure.io import pdbx, pdb, mol
from biotite.structure.io.mol import MOLFile
from biotite.structure.io.pdb import PDBFile
from biotite.structure.io.pdbx import CIFFile

ELEMENT_FIX = {
    "CL": "Cl", "BR": "Br", "SI": "Si",
    "Xx": "H",
}

def extract_sdf_from_cplx(cplx_path, output_sdf, lig_code: str=None):
    if cplx_path.endswith('.cif'):
        struc_array = pdbx.get_structure(
            pdbx.CIFFile.read(str(cplx_path)),
            model=1,
            use_author_fields=False,
            include_bonds=True,
        )
    elif cplx_path.endswith('.pdb'):
        pdb_file_readin = pdb.PDBFile.read(cplx_path)
        struc_array = pdb_file_readin.get_structure(include_bonds=True)
    else:
        raise ValueError("Only support .pdb, .cif and .sdf")
    
    if lig_code is None:
        # `lig_arrays = this_array[this_array.hetero == True]` 
        lig_array = struc_array[(struc_array.res_name=='LIG_L') | (struc_array.res_name=='l01') | (struc_array.res_name=='LIG')]
    else:
        lig_array = struc_array[struc_array.res_name == lig_code]
    
    if lig_array.shape[0] > 0:
        mol_fout = MOLFile()
        mol_fout.set_structure(lig_array)
        mol_fout.write(output_sdf)
        
    return None


def split_cplx_to_arrays(cplx_path, lig_code: str=None):
    if cplx_path.endswith('.pdb'):
        # for Chai1 or MD output
        pdb_file_readin = pdb.PDBFile.read(cplx_path)
        struc_array = pdb_file_readin.get_structure(include_bonds=True,
                                                    model=1)
    else:
        # for protenix
        struc_array = pdbx.get_structure(
            pdbx.CIFFile.read(str(cplx_path)),
            model=1,
            use_author_fields=False,
            include_bonds=True,
        )
        #lig_arrays = this_array[this_array.hetero == True]
    if lig_code is None:
        # `lig_arrays = this_array[this_array.hetero == True]` 
        lig_array = struc_array[(struc_array.res_name=='LIG_L') | (struc_array.res_name=='l01') | (struc_array.res_name=='LIG')]
        protein_array = struc_array[~((struc_array.res_name=='LIG_L') | (struc_array.res_name=='l01') | (struc_array.res_name=='LIG'))]
    else:
        lig_array = struc_array[struc_array.res_name == lig_code]
        protein_array = struc_array[~(struc_array.res_name == lig_code)] 
    

    return lig_array, protein_array


def file_to_biotite_array(file_path, extra_fields:list=None):
    if file_path.endswith('.cif'):
        file = CIFFile.read(file_path)
        biotite_array = pdbx.get_structure(file, include_bonds=True, extra_fields=extra_fields)
    elif file_path.endswith('.pdb'):
        file = PDBFile.read(file_path)
        biotite_array = file.get_structure(include_bonds=True, extra_fields=['atom_id', 'b_factor', 'occupancy'])
    elif file_path.endswith('.sdf'):
        mol_file = MOLFile.read(file_path)
        biotite_array = mol_file.get_structure()
    else:
        raise ValueError("for convertion to biotite array, only .cif/.pdb/.sdf is supported")
    return biotite_array


def biotite_array_to_file(file_path, biotite_array):
    if file_path.endswith('.cif'):
        file = CIFFile()
        pdbx.set_structure(file, biotite_array, include_bonds=True)
        file.write(file_path)
    elif file_path.endswith('.pdb'):
        file = PDBFile()
        file.set_structure(biotite_array)
        file.write(file_path)
    elif file_path.endswith('.sdf'):
        # extract ligand information
        element = biotite_array.element.tolist()
        atoms = [ELEMENT_FIX[e] if e in ELEMENT_FIX else e for e in element] # fix then
        coordinates = list(map(tuple, biotite_array.coord.tolist())) # coordinates -> list[tuple]

        # create Mol
        mol = Chem.RWMol()
        conf = Chem.Conformer(len(atoms)) 
        rdkit_atom_mapping = {}
        for i, (atom, coord) in enumerate(zip(atoms, coordinates)):
            rd_atom = Chem.Atom(atom)
            rd_atom.SetNoImplicit(True)
            idx = mol.AddAtom(rd_atom)
            conf.SetAtomPosition(idx, coord)  
            rdkit_atom_mapping[i] = idx 

        # add conformer
        mol.AddConformer(conf,assignId=True)
        rdDetermineBonds.DetermineConnectivity(mol)
        Chem.MolToMolFile(mol, file_path)
    else:
        raise ValueError("Func `biotite_array_to_file` only support .cif/.pdb/.sdf")
    return None
    
    
def biotite_format_converter(src_path, dst_path):
    biotite_array = file_to_biotite_array(src_path)
    biotite_array_to_file(dst_path, biotite_array)
    return None
    