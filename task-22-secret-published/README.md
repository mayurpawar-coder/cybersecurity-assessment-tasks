# Task 22: The Secret Accidentally Published

## 1. Objective
**Scenario:** a developer pushes a configuration file containing what appears to be an API credential to a **public** repository, then deletes the file 5 minutes later.

**Deliverables:** assess the situation and give a prioritized response plan (immediate response, verification and prevention steps).

## 2. Files
| File | Purpose |
|---|---|
| `README.md` | This write-up: assessment, response plan, verification, root cause, prevention |
| `demo/demo.sh` | Runnable demo on a throwaway local repo with a **fake** key; nothing is pushed anywhere |
| `demo/demo_output.txt` | Output of my run of the demo |
| `screenshots/task22-demo-1.png` | Screenshot of my terminal run |

## 3. Setup
- Git for Windows (includes **Git Bash**) or any Git with a bash shell
- Python 3 and `git-filter-repo`: `pip install git-filter-repo`

## 4. How to run the demo
```
cd task-22-secret-published/demo
bash demo.sh 2>&1 | tee demo_output.txt
```
The script creates a temporary repo in `/tmp/leak-demo`, commits a config file with a fake credential, deletes the file in a second commit, then:
- **Step 4:** shows the secret is still in the history
- **Step 5:** finds it with a scanner-style pattern search
- **Step 6:** removes it with `git filter-repo`

**Expected result:** Step 4 lists both commits and shows the fake key in them. Step 6 prints `after filter-repo:` followed by `0`, meaning the key no longer exists in history.

The key used is AWS's published **example** key (`AKIAIOSFODNN7EXAMPLE`), which is not a real credential.

![Task 22 demo output](screenshots/task22-demo-1.png)

## 5. Assessment: is deleting the file enough? No.
| Fact or assumption | Why it matters |
|---|---|
| Deleting a file only adds a *new* commit. The old commit still contains the secret. | Anyone can see it with `git log -p` or by opening the old commit. **Shown in the demo** (Steps 3 to 5). |
| The repository was public for about 5 minutes. | Public repositories can be cloned, forked and indexed, and automated scanners are known to watch public pushes. So even 5 minutes can be enough for someone to copy the key. I cannot prove either way whether anyone did. |
| Forks, clones, caches and CI logs may hold copies. | Rewriting history in our repository does not remove those copies. Only revoking the credential makes them harmless. |
| The credential "appears to be" real. | It is unverified, but I treat it as **real and compromised until proven otherwise**. A false alarm costs little. A missed leak can cost a lot. |

**Conclusion:** treat this as a confirmed credential exposure. The secret is burned. The fix is to **make the secret worthless** (revoke and rotate), not to hide it.

## 6. Prioritized response plan
| # | When | Action | Why this order |
|---|---|---|---|
| 1 | **0 to 15 min** | **Revoke or rotate the credential** at the provider: disable the key, issue a new one, update the application (environment variable or secret manager). | The only step that actually stops misuse. Everything else is cleanup. |
| 2 | 0 to 15 min | Identify what the key was: which service and account, what permissions, when created, who owns it. | Defines the blast radius. |
| 3 | 15 to 60 min | **Review the provider's audit logs** (for example, AWS CloudTrail) for use of that key from the commit time until revocation: unfamiliar IPs or regions, new users or keys, new resources, data downloads, billing spikes. | Verification: was it abused? |
| 4 | 15 to 60 min | If abuse is found: escalate as a security incident, disable resources or accounts created by the attacker, preserve logs as evidence, notify the owner and management, and follow the legal or breach-notification process if personal data is involved. | Containment and evidence handling. |
| 5 | 1 to 4 hours | **Purge the secret from git history** (only after step 1): `git filter-repo --invert-paths --path config.env --force`, force-push, and ask collaborators to re-clone. Contact the hosting provider if cached views or pull-request references still show it. | Reduces further exposure. Low value if step 1 was skipped. |
| 6 | Same day | Look for **other copies**: other branches and tags, forks, issues and pull requests, CI logs, chat messages, pasted snippets. Scan the whole history for other secrets. | A leak is rarely only one file. |
| 7 | Within days | Write a short blameless post-incident note: timeline, impact, root cause, actions taken, owners. | Root-cause thinking and learning. |

## 7. Verification (how I know it is fixed)
- [ ] The old key returns an authentication error when tested against the provider (revocation confirmed).
- [ ] The new key works and the application is healthy.
- [ ] The audit-log review is finished and the result documented (no abuse, or abuse found and actions taken).
- [ ] `git log --all -p -S"<start of key>"` returns nothing after the history cleanup.
- [ ] A secret scanner such as gitleaks reports zero findings: `gitleaks detect --source . --log-opts="--all"` (newer versions: `gitleaks git`).
- [ ] Forks and other places are checked. Anything unresolved is listed with an owner.

## 8. Root cause (5 Whys)
1. **Why was the secret published?** It was in a file inside the repository.
2. **Why was it in the repository?** The config file mixed secrets with normal settings and was not git-ignored.
3. **Why was it not caught?** There was no pre-commit or CI secret scanning and no push protection.
4. **Why did a developer hold a long-lived, broad credential?** There was no secret manager, no short-lived credentials and no least-privilege policy.
5. **Why did the process allow it?** There was no secrets-handling guideline, no onboarding training and no review gate on config files.

## 9. Preventive recommendations
| Layer | Control |
|---|---|
| Keep secrets out of code | Load secrets from environment variables or a secret manager. Commit only a `config.example` file with placeholders. |
| Stop bad commits | List config and `.env` files in `.gitignore`. Add a **pre-commit hook** with a scanner such as gitleaks. |
| Stop bad pushes | Enable the hosting platform's **secret scanning and push protection**. Make CI fail when a secret is detected. |
| Limit the damage | Use least-privilege keys scoped to one service, **short-lived** tokens, IP restrictions, expiry dates and billing or usage alerts. |
| Detect quickly | Alert on unusual key use and rotate keys regularly. |
| People | Short training and a one-page "I leaked a secret, what now?" runbook (step 1 is always rotate). |

## 10. Assumptions and limits
- I assumed the credential is a cloud or API key with write access. If it were read-only or already expired, the impact would be lower, but the steps would be the same.
- I cannot know whether anyone copied the key. The plan is built so that this does not matter (rotation makes any copy useless).
- Log names and tools differ per provider. A real response would use that provider's own audit tools.
- The demo uses a fake key and a local repo only. It proves the git-history behaviour, not any real-world exploitation.

## 11. References
- GitHub Docs, Removing sensitive data from a repository: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- GitHub Docs, About push protection: https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection
- OWASP, Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- NIST SP 800-61, Incident Response Recommendations: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- gitleaks (open-source secret scanner): https://github.com/gitleaks/gitleaks
- git-filter-repo: https://github.com/newren/git-filter-repo
