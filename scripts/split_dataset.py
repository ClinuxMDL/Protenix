import shutil
from collections import defaultdict
from pathlib import Path

# from pandas.core import frame
import numpy as np
import pandas as pd

np.random.seed(2024)

MD_DATA_DIR = "/hpc-cache-pfs/home/wtl/PDBbind_MD"
AF_DATA_DIR= "/hpc-cache-pfs/home/dataland/af3-dev"
MD_CIF_DIR= "/hpc-cache-pfs/home/dataland/af3-dev/qiaojing/cif5"


in_cluster_fn = f"{AF_DATA_DIR}/qiaojing/cluster_info.csv"

out_md_dir = Path(f"{AF_DATA_DIR}/pdbbind_md_v1")
out_clustered_fn: Path = out_md_dir / "clusters-by-entity-40-and-lig-70.txt"
out_md_dir.mkdir(exist_ok=True, parents=True)

out_md_cif_dir = out_md_dir / "md0805_training_mmcif"
out_md_cif_test1_dir = out_md_dir / "md0805_test1_mmcif"
out_md_cif_test2_dir = out_md_dir / "md0805_test2_mmcif"

if out_md_cif_dir.exists():
    shutil.rmtree(out_md_cif_dir)
if out_md_cif_test1_dir.exists():
    shutil.rmtree(out_md_cif_test1_dir)
if out_md_cif_test2_dir.exists():
    shutil.rmtree(out_md_cif_test2_dir)
out_md_cif_dir.mkdir(exist_ok=True, parents=True)
out_md_cif_test1_dir.mkdir(exist_ok=True, parents=True)
out_md_cif_test2_dir.mkdir(exist_ok=True, parents=True)

def _collect_clustered_frames(data_dir: str) -> dict:
    md_paths = list(Path(data_dir).glob("*_lig_opt"))
    
    results = {}
    for md_path in md_paths:
        frame_fns = list(md_path.glob("post_analysis/representative_frames/cluster_*_frame.pdb"))
        md_name = md_path.name[:4]
        assert md_name not in results, f"{md_name} already in results"
        results[md_name] = len(frame_fns)
    
    return results


def _process_cluster_fn(df: pd.DataFrame, md_info: dict, percent: float = 0.5) -> None:
    training_results = defaultdict(list)
    test1_results = defaultdict(list)
    test2_results = defaultdict(list)
    known_protein_clusters = set()
    known_ligand_clusters = set()
    group_dfs = df.groupby("name")
    print(f'{len(group_dfs)=}')
    num_cluster= 0
    for grp_df_tulpe in group_dfs:
        entity_id, grp_df = grp_df_tulpe
        lig_fn =Path(f"{MD_DATA_DIR}/{entity_id}_lig_opt/inputs/ligands/ligand.sdf")

        if lig_fn.exists():
            shutil.copy(lig_fn, f"{AF_DATA_DIR}/release_data/md0805_sdfs/{entity_id}.sdf")

        grp_df.reset_index(inplace=True, drop=True)
        num_entity= 1
        rand_val = np.random.rand()
        for row_idx, row in grp_df.iterrows():
            md_name = row["name"]
            assert md_name in md_info, f"{md_name} not in md_info"
            frame_cnt = md_info[md_name]
            cluster_id_pro = row["cluster_id_pro"]
            cluster_id_lig = row["cluster_id_lig"]        
            num_entity += 1
            
            if rand_val <= percent and (cluster_id_lig not in known_ligand_clusters) and (cluster_id_pro not in known_protein_clusters):
                for i in range(1, frame_cnt+1):
                    test1_results[cluster_id_pro].append(f"{md_name}_c{i}_{num_entity}")
            
            else:
                known_protein_clusters.add(cluster_id_pro)
                known_ligand_clusters.add(cluster_id_lig)
                for i in range(1, frame_cnt+1):
                    training_results[cluster_id_pro].append(f"{md_name}_c{i}_{num_entity}")
        

    return training_results, test1_results



def main() -> None:
    md_frames_info = _collect_clustered_frames(MD_DATA_DIR)

    df: pd.DataFrame = pd.read_csv(in_cluster_fn)
    cluster_train, cluster_test1= _process_cluster_fn(df, md_frames_info)
    print(f"{len(cluster_train)=}")
    print(f"{len(cluster_test1)=}")
    # print(f"{len(cluster_test2)=}")
    
    with open(str(out_clustered_fn)[:-4]+"_train.txt", "w") as f:
        for cluster_id, frame_names in cluster_train.items():
            for frame_name in frame_names[:10]:
                shutil.copy(f"{MD_CIF_DIR}/{frame_name[:-2]}.cif", f"{out_md_cif_dir}/{frame_name[:-2]}.cif")
            f.write(f"{' '.join(frame_names[:10])}\n")

    with open(str(out_clustered_fn)[:-4]+"_test1.txt", "w") as f:
        num_before = 0
        for cluster_id, frame_names in cluster_test1.items():
            num_before +=1
            if num_before<=100:
                for frame_name in frame_names[:10]:
                    shutil.copy(f"{MD_CIF_DIR}/{frame_name[:-2]}.cif", f"{out_md_cif_test1_dir}/{frame_name[:-2]}.cif")
            else:
                for frame_name in frame_names[:10]:
                    shutil.copy(f"{MD_CIF_DIR}/{frame_name[:-2]}.cif", f"{out_md_cif_test2_dir}/{frame_name[:-2]}.cif")
        
            f.write(f"{' '.join(frame_names)}\n")

    # with open(str(out_clustered_fn)[:-4]+"_test2.txt", "w") as f:
    #     for cluster_id, frame_names in cluster_test2.items():
    #         f.write(f"{' '.join(frame_names)}\n")
    
    print(str(out_clustered_fn)[:-4]+"_train.txt")
    print(str(out_clustered_fn)[:-4]+"_test1.txt")

    



    # print(str(out_clustered_fn)[:-4]+"_test2.txt")



if __name__ == "__main__":
    main()



