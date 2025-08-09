import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from rdkit import Chem
from torch.fx.experimental.symbolic_shapes import Int

MD_DATA_DIR = Path("/hpc-cache-pfs/home/wtl/PDBbind_MD")


def process_once(pdb_dir: Path):
    tmp_fn = pdb_dir / "post_analysis/representative_frames/cluster_info.json"
    pdb_name = pdb_dir.stem[:4]
    with open(tmp_fn, "r") as f:
        cluster_list: list = json.load(f)

    cluster_prob = {}
    for cluster in cluster_list:
        conf_id: int = int(cluster["cluster_order"])
        conf_prob: float = float(cluster["prob"])
        cluster_prob[f"{pdb_name}_c{conf_id}"] = conf_prob
    
    return cluster_prob

def main():
    pdb_dirs = list(MD_DATA_DIR.glob("*_lig_opt"))
    
    cluster_densities = {}
    for pdb_dir in pdb_dirs:
        cluster_densities.update(process_once(pdb_dir))


    cluster_den_fn: Path = "/hpc-cache-pfs/home/dataland/af3-dev/release_data/cluster_densities.json"
    with open(cluster_den_fn, "w") as f:
        json.dump(cluster_densities, f, indent=4)
    
    print(f"{cluster_den_fn=}")

if __name__ == "__main__":
    main()


