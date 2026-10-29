# Cybersecurity Assessment: Task 22 and Task 9

**Candidate:** Mayur Pawar
**Repository:** https://github.com/mayurpawar-coder/cybersecurity-assessment-tasks

I selected two tasks from the Cybersecurity Assessment Task Catalogue:

| Task | Title | Folder | Deliverables (as required by the task) |
|---|---|---|---|
| 22 | The Secret Accidentally Published | [`task-22-secret-published/`](task-22-secret-published/) | Prioritized response plan, verification steps, root cause, preventive recommendations, plus a runnable demo with output and screenshot |
| 9 | Test a Defensive Detection Rule | [`task-9-detection-rule-testing/`](task-9-detection-rule-testing/) | Synthetic logs, test cases, results, improved rule, limitations, runnable code, screenshot |

## Repository layout
```
cybersecurity-assessment-tasks/
|-- README.md                      (this file)
|-- task-22-secret-published/
|   |-- README.md                  (full write-up)
|   |-- demo/demo.sh               (runnable demo, fake key, local only)
|   |-- demo/demo_output.txt       (output of my run)
|   `-- screenshots/task22-demo-1.png
`-- task-9-detection-rule-testing/
    |-- README.md                  (full write-up)
    |-- generate_logs.py, scenarios.py, rules.py, run_tests.py
    |-- logs.csv, ground_truth_labels.csv, results.txt
    `-- screenshots/task9-results.png
```

## Where to start
1. Open each task folder's README. It states the objective, files, setup, execution steps and results.
2. To reproduce the evidence, follow the "Setup" and "How to run" sections in each task's README.

## Important notes
- **All data is synthetic.** No real users, logs, systems or credentials are used. The only "secret" is AWS's published example key, which is not a real credential.
- **AI assistance:** I used an AI assistant to help plan and draft this work. I ran all code and demos myself, the screenshots are from my own runs, and I checked the results and numbers against the output files.
- **Reproducibility:** Task 9 uses only the Python standard library. Task 22 needs Git (with Git Bash) and Python.
