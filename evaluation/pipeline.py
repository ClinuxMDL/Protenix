# -*- encoding: utf-8 -*-
import os
import json
import glob
import tempfile
import collections
import itertools
from tqdm import tqdm

import concurrent.futures
import multiprocessing
from multiprocessing import Pool

from utils.aligner import Aligner
from utils.bond_order import bond_order_mapper, safe_load_mol, save_mol
from utils.converter import biotite_format_converter, biotite_array_to_file, \
                            split_cplx_to_arrays
from utils.interaction_scorer import get_interaction_set, cal_interaction_score
from utils.torsion_score import TorsionScorer


class Pipeline:
    """
    A pipeline for processing and evaluating complex predictions.
    
    This pipeline performs several key operations:
    1. Splits complex structures into protein and ligand components
    2. Corrects bond orders in predicted ligands
    3. Aligns predicted structures to reference and calculates RMSD
    4. Scores interactions between components
    5. Scores torsion distribution
    """
    def __init__(self, reference_cplx, reference_prot, reference_lig, candidate_path):
        """
        Initialize the pipeline with reference and candidate structures.
        Args:
            reference_cplx (str): Path to reference complex structure file (.pdb)
            reference_prot (str): Path to reference protein structure file (.pdb)
            reference_lig (str): Path to reference ligand structure file (.sdf)
            candidate_path (str): Path to candidate prediction file (.cif)
        """
        self.reference_cplx = reference_cplx
        self.reference_prot = reference_prot
        self.reference_lig = reference_lig
        self.pred_cplx_path = candidate_path
        self.pred_prot_path = None
        self.pred_lig_path = None
        
    def _split_cplx(self, pred_prot_path, pred_lig_path):
        """
        Split the predicted complex into separate protein and ligand components.
        
        Args:
            pred_prot_path (str): Path to save predicted protein structure (.pdb)
            pred_lig_path (str): Path to save predicted ligand structure (.sdf)
        """
        # with bond order mapped
        lig_array, prot_array = split_cplx_to_arrays(self.pred_cplx_path)
        biotite_array_to_file(pred_prot_path, prot_array)
        biotite_array_to_file(pred_lig_path, lig_array)
        self.pred_prot_path = pred_prot_path
        self.pred_lig_path = pred_lig_path
        
    def _align_and_cal_rmsd(self):
        """
        Align predicted structures to reference and calculate RMSD.
        
        Returns:
            float: The RMSD between aligned structures
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_sdf_file = os.path.join(tmpdir, "temp.sdf")
            rmsd = Aligner.align_single(self.reference_prot, self.reference_lig,
                                        self.pred_prot_path, self.pred_lig_path,
                                        tmp_sdf_file)
        return rmsd
    
    def _fix_bond_order(self):
        """
        Correct bond orders in predicted ligand using reference as template.
        """
        mol = safe_load_mol(self.pred_lig_path)
        prepared_mol = bond_order_mapper(self.reference_lig,
                                         mol)
        save_mol(prepared_mol, self.pred_lig_path.rstrip('.sdf') + '_with_bo.sdf')

        
    def _interaction_scorer(self):
        """
        Calculate interaction similarity score between reference and candidate, using 
        interaction fingerprint
        
        Returns:
            float: Interaction similarity score
        """
        ref_interaction_set = get_interaction_set(self.reference_cplx, 'LIG')
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_pdb_path = os.path.join(tmpdir, "tmp_cplx.pdb")
            biotite_format_converter(self.pred_cplx_path, tmp_pdb_path)
            candidate_interaction_set = get_interaction_set(tmp_pdb_path, 'l01')
        
        score = cal_interaction_score(ref_interaction_set, candidate_interaction_set)
        return score
    
    def _torsion_scorer(self):
        torsion_score = TorsionScorer.process(self.reference_lig, self.pred_lig_path.rstrip('.sdf') + '_with_bo.sdf')
        return torsion_score
        
    @classmethod
    def process_base(cls, reference_tuple, predicted_tuple):
        reference_cplx, reference_prot, reference_lig = reference_tuple
        predicted_cplx, predicted_prot, predicted_lig = predicted_tuple
        result = {}
        pipe = cls(reference_cplx, reference_prot, reference_lig, predicted_cplx)
        # step1.
        pipe._split_cplx(predicted_prot, predicted_lig)
        pipe._fix_bond_order()
        rmsd = pipe._align_and_cal_rmsd()
        
        torsion_score = pipe._torsion_scorer()
        result['rmsd'] = rmsd
        result['torsion_score'] = torsion_score
        #---run interaction profile evaluation later on--
        #interaction_score = pipe._interaction_scorer()
        #result['interaction_score'] = interaction_score
        return result

    @classmethod
    def interaction(cls, reference_tuple, predicted_tuple):
        reference_cplx, reference_prot, reference_lig = reference_tuple
        predicted_cplx = predicted_tuple[0]
        pipe = cls(reference_cplx, reference_prot, reference_lig, predicted_cplx)
        interaction_score = pipe._interaction_scorer()
        return interaction_score
    
class EvalPipeline:
    """
    A pipeline to evaluate multiple candidate structures against a set of 
    reference structures.
    """
    def __init__(self, ref_dir: str, pred_dir: str):
        """
        Args:
            ref_dir (str): Path to the directory containing reference files.
            pred_dir (str): Path to the directory containing candidate files.
        """
        self.ref_dir = ref_dir  #{pdbcode}_lig_opt/post_analysis_representative_frames/
        self.pred_dir = pred_dir #{base_folder}/seed_{seed}/predictions
        
        ref_cplx_list = glob.glob(f"{ref_dir}/cluster_[0-9]*_frame.pdb")
        pred_cplx_list = glob.glob(f"{pred_dir}/seed_*/predictions/*_sample_[0-9]*.cif")
        # check numbers of predicted complex
        if len(pred_cplx_list) > 100:
            raise ValueError(f"Invalid Number: {pred_cplx_list} for {self.pred_dir}, which should be 100")
        # expand
        self.ref_tuple = [(path, 
                           path.rstrip('.pdb') + '_protein.pdb',
                           path.rstrip('.pdb') + '_ligand_noH.sdf') 
                           for path in ref_cplx_list] 
        
        self.pred_tuple = [(path,
                            path.rstrip('.cif') + '_prot.pdb',
                            path.rstrip('.cif') + '_ligand.sdf')
                            for path in pred_cplx_list] 
        
        
    @staticmethod
    def _process_single_prediction(args):
        pred_files, ref_tuple, ref_dir, pred_dir = args
        group_results = []
        for ref_files in ref_tuple:
            ref_cplx = ref_files[0]
            try: 
                    result_single = Pipeline.process_base(ref_files, pred_files)
                    result_entry = {
                        'input_profile': (pred_files, ref_files),
                        'reference_complex': os.path.basename(ref_cplx),
                        **result_single
                    }
                    
                    group_results.append(result_entry)

            except Exception as e:
                # continue
                error_entry = {
                    'reference_complex': os.path.basename(ref_cplx),
                    'error': str(e)
                }
                
        if not group_results:
            return None
        
        # 1. find index of minimum RMSD
        min_rmsd_entry = min(group_results, key=lambda x: x['rmsd'])
        min_rmsd = min_rmsd_entry['rmsd']
        ref_at_min_rmsd = min_rmsd_entry['reference_complex']
        
        min_rmsd_file_profile = min_rmsd_entry['input_profile']
        pred_files, ref_files = min_rmsd_file_profile
        ref_cplx = ref_files[0]
        
        interation_score_of_min_rmsd = Pipeline.interaction(ref_files,
                                                            pred_files)
        
        # 2. find min torsion score
        min_torsion_entry = min(group_results, key=lambda x: x['torsion_score'])
        min_torsion_score = min_torsion_entry['torsion_score']
        ref_at_min_torsion = min_torsion_entry['reference_complex']
        
        packed_results = {
        'min_rmsd': min_rmsd,
        'interaction_score_at_min_rmsd': interation_score_of_min_rmsd,
        'reference_for_min_rmsd': ref_at_min_rmsd,
        'min_torsion_score': min_torsion_score,
        'reference_for_min_torsion': ref_at_min_torsion,
        'ref_dir': ref_dir,
        'candidate_dir': pred_dir
        }
        
        return packed_results
                    
    
    def run(self, output_json: str=None, n_workers: int=None, parallel_style: str="concurrent"):
        """
        Executes the evaluation pipeline
        
        Return:
            Mean_RMSD: Average value of `min_rmsd` for each candidate
            Torsion_score: average torsion score
            Interaction_score: average `interaction_score_of_min_rmsd`
        """
        
        if n_workers is None:
            n_workers = os.cpu_count()
            
        tasks = [(pred_files, self.ref_tuple, self.ref_dir, self.pred_dir) for pred_files in self.pred_tuple]
        
        if len(tasks) < 50:
            return 5, 0, 0
            
        if parallel_style == "concurrent":
            with concurrent.futures.ProcessPoolExecutor(max_workers=n_workers) as executor:
                results_iterator = executor.map(self._process_single_prediction, tasks)
                final_results = list(tqdm(results_iterator, total=len(self.pred_tuple), desc="Evaluating predicted result"))
        
        elif parallel_style == "mp":
            with Pool(processes=n_workers) as pool:
                results_iterator = pool.imap_unordered(self._process_single_prediction, tasks)
                final_results = list(tqdm(results_iterator, total=len(self.pred_tuple), desc="Evaluating (multiprocessing)"))
        
        else:
            raise ValueError(f"Unknown parallel_style: '{parallel_style}'. Choose 'concurrent' or 'mp'.")
        
        # post process
        final_results = [res for res in final_results if res is not None]
        
        if output_json is not None:
            with open(output_json, 'w') as f:
                for item in final_results:
                    json_string = json.dumps(item)
                    f.write(json_string + '\n')

        # aggregate result
        mean_rmsd = sum(x['min_rmsd'] for x in final_results) / 100
        torsion_score = sum(x['min_torsion_score'] for x in final_results) / 100 
        interaction_score = sum(x['interaction_score_at_min_rmsd'] for x in final_results) / 100

        return mean_rmsd, torsion_score, interaction_score
    
    def _rmsd_score(self, rmsd):
        if rmsd >= 5.0:
            return 0.0
        elif rmsd >= 2.0:
            # linear range
            return (5.0 - rmsd) / 6.0
        elif rmsd > 0:
            # 1A -> 0.85
            return -0.1 * (rmsd ** 2) - 0.05 * rmsd + 1.0
        elif rmsd == 0:
            return 1.0
        else:
            return 0.0
    
    def _torsion_score(self, torsion_diff):
        return (1 - torsion_diff / 180) ** 2
        
        
    @classmethod
    def exec(cls, ref_dir: str, pred_dir: str, output_json: str=None, n_workers: int = None, parallel_style = "mp", weights: list=[0.6, 0.2, 0.2]):
        evalpipe = cls(ref_dir, pred_dir)
        mean_rmsd, torsion_diff, interaction_score = evalpipe.run(output_json, n_workers=n_workers, parallel_style=parallel_style)
        rmsd_score = evalpipe._rmsd_score(mean_rmsd)
        torsion_score = evalpipe._torsion_score(torsion_diff)
        assert sum(weights) == 1, 'the total weights should equal to 1!'
        overall_score = rmsd_score * weights[0] + torsion_score * weights[1] + interaction_score * weights[2]
        packed_result = {'rmsd': mean_rmsd,
                          'rmsd_score': rmsd_score,
                          'torsion_diff': torsion_diff,
                         'torsion_score': torsion_score,
                         'interaction_score': interaction_score,
                         'total_score': overall_score}
        
        
        return packed_result

    
if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)
    

    
    