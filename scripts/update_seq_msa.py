import json
import shutil
from pathlib import Path

import pandas as pd


def read_fasta_list(batch_msa_dir:Path):
    count = 0
    batch_seqs = []
    seq_fns = list(batch_msa_dir.glob("*/pairing.a3m"))
    batch_seqs = [""] * len(seq_fns)
    for fn in seq_fns:
        batch_i = int(fn.parent.stem)
        with open(fn, "r") as f:
            for line in f:
                if line[:1] == ">":
                    count +=1
                    continue
                batch_seqs[batch_i] = line.strip()
                break
    return batch_seqs

def update_seq_info(seq2id:dict, batch_seqs: list, batch_msa_dir: Path, output_dir:Path):
    cur_id = len(seq2id)
    for i, seq in enumerate(batch_seqs):
        if seq not in seq2id:
            seq2id[seq] = cur_id
            tmp_out_dir = output_dir / f"{cur_id}"
            tmp_out_dir.mkdir(parents=True, exist_ok=True)
            tmp_msa_dir = batch_msa_dir / f"{i}"
            tmp_pair_fn = tmp_msa_dir / "pairing.a3m"
            tmp_unpair_fn = tmp_msa_dir / "non_pairing.a3m"
            assert tmp_pair_fn.exists()
            assert tmp_unpair_fn.exists()
            shutil.copy(tmp_pair_fn, tmp_out_dir / f"uniref100_hits.a3m")
            shutil.copy(tmp_unpair_fn, tmp_out_dir / f"mmseqs_other_hits.a3m")
            cur_id += 1

    return seq2id


            
def main():
    input_dir = Path("/hpc-cache-pfs/home/tanwenjuan/Protenix/data_msa/data_msa")
    seq_json_fn = Path("/hpc-cache-pfs/home/dataland/af3-dev/release_data/seq_to_pdb_index.json")
    
    output_dir = Path("/hpc-cache-pfs/home/dataland/af3-dev/release_data/new_msa")
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


    with open(seq_json_fn, "r",) as f:
        seq2id = json.load(f)
    for i in range(1,162):
        # fasta_fn = input_dir / f"ppibind_batch_{i}.fasta"
        batch_msa_dir = input_dir.parent / f"output_msa/batch_{i}"
        # assert fasta_fn.exists()
        assert batch_msa_dir.exists()
        batch_seqs = read_fasta_list(batch_msa_dir)
        seq2id =update_seq_info(seq2id, batch_seqs, batch_msa_dir, output_dir)

    out_json_fn = output_dir.parent / "seq_to_pdb_index_v2.json"
    with open(out_json_fn, "w") as f:
        json.dump(seq2id, f, indent=4)
    print(f"{out_json_fn=}")


if __name__ == "__main__":
    main()