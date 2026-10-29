# Task 9: Test a Defensive Detection Rule

## 1. Objective
Take a detection rule, test it against synthetic logs, find the **false positives** (alerts that should not fire) and the **missed cases** (attacks it does not catch), and propose an improved rule.

All data here is **synthetic**. No real users, IPs or credentials. The IP addresses come from ranges reserved for documentation (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) and shared address space (100.64.0.0/10).

## 2. Files
| File | Purpose |
|---|---|
| `generate_logs.py` | Creates the synthetic login logs (`logs.csv`) and the hidden answer key (`ground_truth_labels.csv`) |
| `scenarios.py` | Lists the 10 test scenarios and whether each one **should** raise an alert |
| `rules.py` | Contains the supplied rule (v1) and my improved rules (v2) |
| `run_tests.py` | Runs both rules on the logs, prints the results table and writes `results.txt` |
| `logs.csv` | 154 synthetic login events (event_id, timestamp, user, src_ip, status) |
| `ground_truth_labels.csv` | Which scenario each event belongs to (kept separate, so the rules never see it) |
| `results.txt` | Saved output of the test run |
| `screenshots/task9-results.png` | Screenshot of my terminal run |

## 3. Setup
- Python 3.8 or newer. **No extra packages**, standard library only.
- Open a terminal in this folder (`task-9-detection-rule-testing`).

## 4. How to run
```
python generate_logs.py
python run_tests.py
```
(On Windows, use `py` instead of `python` if `python` is not recognised.)

`generate_logs.py` prints `wrote 154 events`. `run_tests.py` prints the results table and writes `results.txt`. The logs are generated with a fixed random seed, so every run gives the same data and the same results.

## 5. The rule under test (v1)
> Alert when a single source IP has **5 or more failed logins within 5 minutes**.

The task did not include a rule file, so I used this very common baseline brute-force rule as the "supplied" rule.

## 6. Method
1. **Hypothesis:** a per-IP, 5-minute counter catches fast brute force, but (a) misses slow or distributed attacks and (b) raises false alarms on shared IPs such as an office NAT.
2. I built **10 labelled scenarios** (154 events in total): normal traffic, several attack styles, and tricky benign cases.
3. I wrote down the expected answer ("should this alert?") for each scenario in `scenarios.py` **before** running the rule.
4. I ran v1, compared the alerts with the expected answers, found the problems, then built v2 and ran it again on the same data.

Result labels: **TP** = attack correctly alerted, **TN** = normal traffic correctly ignored, **FP** = false alarm, **FN** = attack missed.

## 7. Test cases and results (actual output, saved in `results.txt`)
```
Events: 154   |   v1 alerts: 3   |   v2 alerts: 5

ID  Should alert  v1                              v2                          Description
--------------------------------------------------------------------------------------------------------------
S00 False         TN                              TN                          Normal background logins + lone typos
S01 True          TP V1/MEDIUM                    TP R1/MEDIUM                Classic brute force: 8 fails/2 min, 1 IP -> 1 account
S02 True          FN (missed)                     TP R2/HIGH                  Slow password spray: 1 IP, 20 users, 1 try/2 min, no success
S03 True          FN (missed)                     TP R3/HIGH                  Distributed attack on 1 account from 10 IPs in 6 min
S04 False         FP (false alarm) V1/MEDIUM      TN                          Office NAT: 6 users mistype once then succeed (same IP)
S05 False         TN                              TN                          Single user forgets password: 3 fails then success
S06 False         TN                              TN                          Boundary: exactly 4 fails, below threshold
S07 True          TP V1/MEDIUM                    TP R1/CRITICAL              Brute force that ends in SUCCESS (likely compromise)
S08 True          FN (missed)                     TP R1/MEDIUM                Low-and-slow brute force: 12 fails over 24 min
S09 True          FN (missed)                     FN (missed)                 Botnet spray: 30 IPs x 30 users, 1 fail each

v1: TP=2 FP=1 FN=4 TN=3  precision=0.67 recall=0.33
v2: TP=5 FP=0 FN=1 TN=4  precision=1.00 recall=0.83

v2 alert detail:
  2026-10-27 09:06:00  MEDIUM    R1 brute-force ip+user           key=203.0.113.10|admin  (5 events)
  2026-10-27 09:10:00  HIGH      R2 password-spray ip             key=203.0.113.20  (5 events)
  2026-10-27 09:21:30  MEDIUM    R1 brute-force ip+user           key=203.0.113.40|admin2  (10 events)
  2026-10-27 09:24:12  HIGH      R3 distributed-user              key=finance.lead  (8 events)
  2026-10-27 09:50:52  CRITICAL  R1 brute-force ip+user           key=203.0.113.30|svc.backup  (5 events)
```

Screenshot of my run:

![Task 9 test results](screenshots/task9-results.png)

**Metrics:** precision = TP / (TP + FP), recall = TP / (TP + FN).
- v1: TP 2, FP 1, FN 4, TN 3, so precision = 2/3 = 0.67 and recall = 2/6 = 0.33
- v2: TP 5, FP 0, FN 1, TN 4, so precision = 5/5 = 1.00 and recall = 5/6 = 0.83

## 8. What went wrong with v1
| Finding | Scenario | Why |
|---|---|---|
| **False positive** | S04 office NAT | 6 different staff each mistype once behind one IP, so the per-IP count reaches 6 in 3 minutes. All six logged in successfully a moment later, so this is normal behaviour. |
| **Missed** | S02 slow password spray | One try per user every 2 minutes, so only 3 failures fall inside any 5-minute window. |
| **Missed** | S08 low-and-slow brute force | One try every 2 minutes against one account (12 in total), so it never reaches 5 in 5 minutes. |
| **Missed** | S03 distributed attack | 10 different IPs try one account once each, so no single IP crosses the threshold. |
| **Missed** | S09 botnet spray | 30 IPs x 30 users, one failure each. |
| **Weak** | S07 brute force that succeeds | It alerted, but with the same MEDIUM severity as a failed attack, although here the attacker got in. |

## 9. Improved rule set (v2)
| Rule | Logic | What it fixes |
|---|---|---|
| R1 brute force | Per **IP + user**: 5 or more failures in 5 min, **or** 10 or more in 30 min | S04 false alarm (different users no longer add up); S08 slow attack |
| R1 escalation | Failures followed by a **success** for the same IP and user: severity **CRITICAL** | S07 severity |
| R2 password spray | One IP with failures for **5 or more distinct users** within 30 min **and zero successes** from that IP in that window | S02; the "no success" condition keeps the NAT case (S04) quiet |
| R3 distributed | One user with 8 or more failures in 10 min from **3 or more distinct IPs** | S03 |

**Result:** v1 precision 0.67 and recall 0.33, improved to v2 precision 1.00 and recall 0.83. False positives dropped from 1 to 0, and missed attacks from 4 to 1.

## 10. Limitations
- **S09 is still missed.** One failure per IP and per user is invisible to per-key counters. It needs a global baseline (for example, alert when total failed logins in 10 minutes exceed about 3 times the normal rate) or IP-reputation feeds.
- The thresholds (5, 10, 8 and the time windows) are my judgement on a small synthetic set. In production they must be tuned on real baseline data. A perfect score here does **not** mean the rules would be perfect on real traffic.
- R2's "no success" condition can be gamed: an attacker who also logs in once from that IP would suppress it. A success-ratio condition would be more robust.
- A low-volume real attack from a shared NAT IP could hide among legitimate traffic. Allow-listing known NAT IPs needs care and regular review.
- The rules only use login events. They do not use geo-location, device, user-agent or MFA data.

## 11. Recommendation
Deploy R1 and R3 first (low false-positive risk). Run R2 in alert-only mode for a week to tune it. Send CRITICAL alerts (failures followed by success) to immediate analyst triage. Add a global failure-rate baseline alert to cover the botnet case.

## 12. References
- MITRE ATT&CK, T1110 Brute Force: https://attack.mitre.org/techniques/T1110/
- MITRE ATT&CK, T1110.003 Password Spraying: https://attack.mitre.org/techniques/T1110/003/
