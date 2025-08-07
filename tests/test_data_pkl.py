import gzip
import pickle

lib_pkl = "/hpc-cache-pfs/home/dataland/mmp_lib_max_diff10.pkl.gz"
with gzip.open(lib_pkl, 'rb') as f:
    smriks_dict = pickle.load(f)


with open("./mmp_lib_max_diff10.csv", "w") as f:
    f.write("source,target\n")
    for key, values in smriks_dict.items():
        for val_ in values:
            f.write(f"{key},{val_}\n")


