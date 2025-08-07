import sys

import pandas as pd

csv_fn = sys.argv[1]

df = pd.read_csv(csv_fn)

sub_df = df.query('eval_type == "ligand_prot"')
sub_df.reset_index(drop=True, inplace=True)
with open(csv_fn[:-4] +"_ligand_prot.csv", "w") as f:
    sub_df.to_csv(f, index=False)
