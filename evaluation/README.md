### **Evaluation of Testset1**

This section is configured to evaluate your checkpoint's performance on the benchmark evaluation set.

The evaluation pipeline utilizes multiple CPU workers for parallel processing. During the initial phase, partial results will be stored in the `PARTIAL_RESULT_DIR`. Once the first phase completes, you should proceed to run `step2.sh`to aggregate and merge the final results.

#### **EntryPoint**

**Step1**

Submit to Volcano Engine using multiple workers. (Performance reference: 128vCPUs × 10 workers = 300s processing time)

```bash
bash step1.sh
```

**Step2 (After Step1 finished)**

```bash
bash step2.sh {PARTIAL_RESULT_DIR}
```

Final benchmark scores (Avg_Score) are written to the last line of {PARTIAL_RESULT_DIR}/final_results.csv.
