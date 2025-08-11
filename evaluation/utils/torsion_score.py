import sys
import glob
import numpy as np
from rdkit import Chem
from rdkit.Chem import rdMolTransforms
from rdkit.Chem.Lipinski import RotatableBondSmarts

class TorsionScorer:
    def __init__(self, weights=None):
        self.weights = weights
    
    def __call__(self, reference_sdf, query_sdf):
        # get torsion atom idx
        torsions = find_rotatable_torsions(reference_sdf)
        # calc torsion angles for reference and query sdfs
        reference_torsion_angles = calc_torsion_angle(reference_sdf, torsions)
        query_torsion_angles = calc_torsion_angle(query_sdf, torsions)
        
        angle_diff = calc_angle_diff_avg(reference_torsion_angles, query_torsion_angles, self.weights)
        return angle_diff
    
    @classmethod
    def process(cls, reference_sdf, query_sdf, weights=None):
        rot_calculator = cls(weights)
        torsion_diff = rot_calculator(reference_sdf, query_sdf)
        return torsion_diff

def find_rotatable_torsions(sdf):
    mol = Chem.SDMolSupplier(sdf)[0]
    rotatable_bonds = mol.GetSubstructMatches(RotatableBondSmarts)
    torsions = []
    for i, (a_idx, b_idx) in enumerate(rotatable_bonds):
        atom_a = mol.GetAtomWithIdx(a_idx)
        atom_b = mol.GetAtomWithIdx(b_idx)
        neighbor_a = [neighbor.GetIdx() for neighbor in atom_a.GetNeighbors() if neighbor.GetIdx() != b_idx][0]
        neighbor_b = [neighbor.GetIdx() for neighbor in atom_b.GetNeighbors() if neighbor.GetIdx() != a_idx][0]
        torsions.append((neighbor_a, a_idx, b_idx, neighbor_b))
    return torsions

def calc_torsion_angle(sdf, torsions):
    mol = Chem.SDMolSupplier(sdf)[0]
    conf = mol.GetConformer()
    torsion_angles = []
    for (i,j,k,l) in torsions:
        angle = rdMolTransforms.GetDihedralDeg(conf, i,j,k,l)
        torsion_angles.append(angle)
    return torsion_angles

def angle_diff(angle1, angle2):
    """Calculate the difference between two angles considering periodicity."""
    diff = angle1 - angle2
    diff = abs((diff + 180) % 360 - 180)
    return diff

def calc_angle_diff_avg(torsion_angles1, torsion_angles2, weights=None):
    if weights is None:
        weights = np.ones(len(torsion_angles1))
    else:
        weights = np.array(weights)
    angle_diff_list = [angle_diff(a1, a2) for a1, a2 in zip(torsion_angles1, torsion_angles2)]
    angle_diff_arr = np.array(angle_diff_list)
    angle_diff_avg = np.sum(angle_diff_arr * weights) / np.sum(weights)
    return angle_diff_avg
