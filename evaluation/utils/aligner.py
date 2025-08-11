# -*- encoding: utf-8 -*-
import os
import numpy as np

from rdkit import Chem
from rdkit.Chem import rdFMCS
from copy import deepcopy
from pymol import cmd, stored
from posebusters.modules.rmsd import check_rmsd

class Aligner:
    def __init__(self, prot_ref, lig_ref):
        self.prot_ref = prot_ref
        self.lig_ref = lig_ref
    
    @classmethod
    def align_single(cls, prot_ref, lig_ref, prot_pred, lig_pred, lig_save_path):
        aligner = cls(prot_ref, lig_ref)
        rmsd = aligner(prot_pred, lig_pred, lig_save_path)
        return rmsd
    
    def __call__(self, prot_pred, lig_pred, lig_save_path):
        # Init pymol
        cmd.reinitialize()
        cmd.set("retain_order", 1)

        # load reference protein and ligand
        cmd.load(self.prot_ref, "crystal_prot")
        cmd.remove("crystal_prot and (elem H or name H*)")
        cmd.load(self.lig_ref, "crystal_lig")
        cmd.remove("crystal_lig and (elem H or name H*)")
        cmd.select("reference_pocket", 
                    "br. (%crystal_prot and name CA+C+N) w. 10.0 for (%crystal_lig and not h.)")
        
        # Load predicted protein and ligand
        cmd.load(prot_pred, "predicted_protein")
        cmd.remove("predicted_protein and (elem H or name H*)")
        cmd.load(lig_pred, "predicted_ligand")
        cmd.remove("predicted_ligand and (elem H or name H*)")
        cmd.select("predicted_pocket",
                "br. (%predicted_protein and name CA+C+N) w. 10.0 for (%predicted_ligand and not h.)")


        # Align
        cmd.align("predicted_pocket", "reference_pocket")
        cmd.matrix_copy("predicted_protein", "predicted_ligand")

        cmd.save(lig_save_path, "predicted_ligand",format="sdf")
        
        aligned_rmsd = cmd.align("predicted_ligand","crystal_lig")[0]
        
        if aligned_rmsd == 0:
            return self._aligner_backup(lig_save_path)
        else:  
            return aligned_rmsd
    
    def _aligner_backup(self, lig_save_path):
        predicted_ligand = Chem.MolFromMolFile(lig_save_path)
        crystal_ligand = Chem.MolFromMolFile(self.lig_ref)
        
        mol_gen, mol_ref = deepcopy(predicted_ligand), deepcopy(crystal_ligand)
        
        # Extract coordinates
        coordinates_lig2 = mol_gen.GetConformer().GetPositions()
        coordinates_lig1 = mol_ref.GetConformer().GetPositions()
        
        # FindMCS
        res = rdFMCS.FindMCS([mol_gen, mol_ref])
        mcs_mol = Chem.MolFromSmarts(res.smartsString) # extract MCS as rdkit.Chem.Mol
        mas1 = list(mol_ref.GetSubstructMatch(mcs_mol)) # match reference first
        mas2_list = mol_gen.GetSubstructMatches(mcs_mol, uniquify=False) # match mol_gen then 
        if len(mas2_list) == 0: 
            # Fail to match (seems impossible)
            # If so, applying final backup (posebuster.modules.rmsd.check_rmsd)
            return check_rmsd(predicted_ligand, crystal_ligand)["results"]["rmsd"] 

        # Reorder coordinates leveraging MCS 
        coordinates_lig1 = coordinates_lig1[mas1]
        list_rmsd = []
        for match1 in mas2_list:
            coordinates_lig2_tmp = coordinates_lig2[list(match1)]
            diff = coordinates_lig2_tmp - coordinates_lig1
            list_rmsd.append(np.sqrt((diff * diff).sum() / len(coordinates_lig2_tmp)))
        # Return the minimum RMSD
        rmsd = min(list_rmsd)
        return rmsd

