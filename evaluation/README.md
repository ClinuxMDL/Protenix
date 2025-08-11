### **Evaluation of Testset1**

This section is configured to evaluate your checkpoint's performance on the benchmark evaluation set.

The evaluation pipeline utilizes multiple CPU workers for parallel processing. During the initial phase, partial results will be stored in the `PARTIAL_RESULT_DIR`. Once the first phase completes, you should proceed to run `step2.sh`to aggregate and merge the final results.

#### **EntryPoint**

**Step0**
Infer 100 cifs with the specific checkpoint.
Submit to Volcano Engine using multiple GPU workers. (Performance reference: 1 Gpus × 8 workers, 25 min processing time)。 Copy the task with the name "task_step0_infer_cifs_v1" and modify the command to:

```bash
source /root/miniconda3/bin/activate
cd {your_protenix_dir}
bash evaluation/step0.sh {your_ckpt_fn} {Test1 or Test2}
```

**Step1**

Submit to Volcano Engine using multiple CPU workers. (Performance reference: 128vCPUs × 10 workers = 300s processing time)。 Copy the task with the name "task_step1_scoring_v1" and modify the command to:

```bash
source /root/miniconda3/bin/activate
cd {your_protenix_dir}
bash evaluation/step1.sh {RESULT_DIR}
```

**Step2 (After Step1 finished)**

run this command on your local machine.
```bash
bash evaluation/step2.sh {PARTIAL_RESULT_DIR}
```

Final benchmark scores (Avg_Score) are written to the last line of {PARTIAL_RESULT_DIR}/final_results.csv.
