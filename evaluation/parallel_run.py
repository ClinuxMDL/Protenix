import os
import sys
import pandas as pd

from pipeline import EvalPipeline


META_CSV_PATH = os.environ.get("META_CSV_PATH", "example/testset1_metadata.csv")
BASE_DIR_REF = os.environ.get("BASE_DIR_REF", "example/ref_set/reference")
BASE_DIR_PRED = os.environ.get("BASE_DIR_PRED", "example/results/testset1")
PARTIAL_RESULTS_DIR = os.environ.get("PARTIAL_RESULTS_DIR", "example/results/PART_testset1")

def get_parallel_config():
    try:
        worker_index = int(os.environ['MLP_ROLE_INDEX'])
        num_workers = int(os.environ[f'MLP_WORKER_NUM'])
    except (KeyError, ValueError) as e:
        print(e)
        sys.exit(1)
    return worker_index, num_workers


def main():
    worker_index, num_worker = get_parallel_config()
    df_all_tasks = pd.read_csv(META_CSV_PATH)
    all_codes = sorted(list(df_all_tasks.name.unique()))
    
    codes_to_process = [code for i, code in enumerate(all_codes) if i % num_worker == worker_index]
    print(codes_to_process)
    if not codes_to_process:
        return 
    
    results = {}
    for code in codes_to_process:
        reference_dir = os.path.join(BASE_DIR_REF, f"{code}_lig_opt", 'post_analysis', 'representative_frames')
        pred_dir = os.path.join(BASE_DIR_PRED, f'{code.upper()}')
        
        if not os.path.isdir(reference_dir) or not os.path.isdir(pred_dir):
            print(reference_dir)
            print(pred_dir)
            print(f"SKIP {code}")
            continue
        
        packed_metrics = EvalPipeline.exec(reference_dir, pred_dir, output_json=None)
        results[code] = packed_metrics
        
        
    if not results:
        return
    
    df_partial = pd.DataFrame.from_dict(results, orient='index')
    df_partial.index.name = 'name' 
    df_partial.reset_index(inplace=True)
    os.makedirs(PARTIAL_RESULTS_DIR, exist_ok=True)
    output_path = os.path.join(PARTIAL_RESULTS_DIR, f"partial_results_{worker_index}.csv")
    df_partial.to_csv(output_path, index=False)

    
if __name__ == "__main__":
    main()