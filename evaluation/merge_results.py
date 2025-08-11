import os
import pandas as pd

from glob import glob

PARTIAL_RESULTS_DIR = os.environ.get("PARTIAL_RESULTS_DIR", None)

def merge(result_partial_dir, output=None):
    paths = list(glob(f"{result_partial_dir}/*.csv")) 
    list_of_dataframes = [pd.read_csv(f) for f in paths]
    final_df = pd.concat(list_of_dataframes, ignore_index=True)
    final_df.sort_values(by='name', inplace=True)
        
    final_score = final_df.total_score.mean()
    
    if output:
        new_row = pd.DataFrame([{'name': 'Avg_Score', 'total_score': final_score}])
        final_df = pd.concat([final_df, new_row], ignore_index=True)
        final_df.to_csv(output, index=False)
    
    return final_score

def main():
    if PARTIAL_RESULTS_DIR:
        score =  merge(PARTIAL_RESULTS_DIR, os.path.join(PARTIAL_RESULTS_DIR,'final_results.csv'))
    else:
        score = None
    return score


if __name__ == "__main__":
    score = main()
    print(score)
    
        


    