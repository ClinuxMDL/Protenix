# -*- encoding: utf-8 -*-
import os
import json

import plip
import plip.basic
from plip.structure.preparation import PDBComplex

INTERACTION_SET = {'saltbridge_lneg':['resnr', 'restype', 
                                'negative.atoms[0].idx'],
                   'saltbridge_pneg':['resnr', 'restype', 
                                'positive.atoms[0].idx'],
                'all_hbonds_ldon':['restype','atype','d.idx'], 
                'all_hbonds_pdon': ['restype','atype','a.idx'],
                'hydrophobic_contacts':['resnr','restype'],
                'halogen_bonds':['donortype','acctype'],
                'pistacking': ['resnr','restype','ligandring.atoms[0].idx']}

def get_interaction_fingerprint(interaction, interaction_type):
    # get fingerprint by key attributes of a single interaction item
    value_list = []
    i_key = INTERACTION_SET[interaction_type]
    for k in i_key:
        attr_chain = k.split('.')
        current_obj = interaction
        for attr in attr_chain:
            if '[' in attr and ']' in attr:
                attr_name, index = attr.split('[')
                index = int(index[:-1])
                current_obj = getattr(current_obj, attr_name, None)
                if current_obj is not None and isinstance(current_obj, list):
                    current_obj = current_obj[index]
                else:
                    return None
            else:
                current_obj = getattr(current_obj, attr, None)
        value_list.append(str(current_obj))
    
    values = ''.join(value_list)
    return interaction_type + values


def get_interaction_profile(pdb_file, lig_id, wo_babel=False, exclude_hydro=True):
    plip.basic.config.NOHYDRO = wo_babel
    cplx_parser = PDBComplex()
    cplx_parser.load_pdb(str(pdb_file))
    cplx_parser.analyze()
    
    # assign complete ligand id
    ligand_title = ""
    for ligand in cplx_parser.ligands:
        if lig_id in ligand.mol.title:
            ligand_title = ligand.mol.title
            break
        
    if not ligand_title:
        ligand_title = cplx_parser.ligands[0].mol.title
    
    interaction_set = cplx_parser.interaction_sets[ligand_title]
    
    interaction_profile = {}
    interaction_key = ['pistacking', 'all_hbonds_ldon', 'all_hbonds_pdon', 'hydrophobic_contacts', 'saltbridge_lneg', 'saltbridge_pneg']
    
    if exclude_hydro:
        interaction_key.remove('hydrophobic_contacts')
        
    for k in interaction_key:
        interaction_profile[k] = getattr(interaction_set, k, None)

    return interaction_profile
    
def get_interaction_set(pdb_file, lig_id, wo_babel=False, exclude_hydro=True) -> tuple:
    profile_set = set()
    interaction_profiles:dict = get_interaction_profile(pdb_file, lig_id, wo_babel, exclude_hydro)
    
    for interaction_type, all_interactions in interaction_profiles.items():
        for interaction in all_interactions:
            _itr_profile = get_interaction_fingerprint(interaction, interaction_type)
            if _itr_profile is not None:
                profile_set.add(_itr_profile)
        
    return profile_set

def cal_interaction_score(ref_interaction_set:set, candidate_interaction_set:set) -> float:
    if len(ref_interaction_set) == 0:
        return 1.0
    interaction_overlap_score = len(ref_interaction_set & candidate_interaction_set) / len(ref_interaction_set)
    return interaction_overlap_score
    
