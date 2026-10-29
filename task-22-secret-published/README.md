# Task 22 — The Secret Accidentally Published

**Scenario:** a developer pushes a config file containing what looks like an API credential to a **public** repository, then deletes the file 5 minutes later.

## 1. Assessment: is deleting it enough? No.
| Fact / assumption | Why it matters |
|---|---|
| Deleting a file only adds a *new* commit. The old commit still contains the secret. | Anyone can run `git log -p` or browse the old commit. **Proven in the demo** (`demo/demo_output.txt`, steps 3-5). |
| The repo was public for ~5 minutes. | Public repos can be cloned, forked, and indexed. Automated scanners watch public pushes continuously, so 5 minutes is enough for exploitation. I cannot prove anyone copied it, but I also cannot prove nobody did. |
| Forks, clones, search caches and CI logs may hold copies. | Rewriting history in our repo does not remove those. Only revoking the credential neutralises them. |
| "What appears to be" a credential. | Unverified. Still treat it as **real and compromised until proven otherwise** (cost of a false alarm is small; cost of a missed leak is large). |

**Conclusion:** treat this as a confirmed credential exposure. The secret is burned. The fix is to **make the secret worthless**, not to hide it.

## 2. Prioritised response plan
| # | When | Action | Why this order |
|---|---|---|---|
| 1 | **0-15 min** | **Revoke / rotate the credential** at the provider (disable the key, issue a new one, update the app via env var or secret manager). | Only step that actually stops misuse. Everything else is cleanup. |
| 2 | 0-15 min | Identify exactly what the key was: which service, which account, what permissions, when created, who owns it. | Defines the blast radius. |
| 3 | 15-60 min | **Check provider audit logs** for use of that key between the commit time and revocation (and before, if it's older): unfamiliar IPs, new regions, new resources, new users/keys, data downloads, billing spikes. | Verification: was it abused? |
| 4 | 15-60 min | If abuse is found: escalate as a security incident, disable created resources/accounts, preserve logs, notify owner/management, follow the legal/breach-notification process if personal data is involved. | Containment and evidence handling. |
| 5 | 1-4 h | **Purge from git history** (after step 1): `git filter-repo --invert-paths --path config.env --force`, force-push, ask collaborators to re-clone. Request cache/cached-view removal from the host's support if needed. | Reduces further exposure; low value if step 1 was skipped. |
| 6 | Same day | Search for **other copies**: other branches/tags, forks, issues/PRs, CI logs, Slack/chat, wikis, pasted snippets. Scan the whole repo history for other secrets. | The leak is rarely only one file. |
| 7 | Within days | Write a short blameless post-incident note: timeline, impact, root cause, actions, owners. | Root-cause and learning. |

## 3. Verification (how I know it's really fixed)
- [ ] Old key returns an authentication error when tested against the provider (revocation confirmed).
- [ ] New key works; application is healthy.
- [ ] Audit-log review completed and result documented (no abuse / abuse found + actions).
- [ ] `git log --all -p -S"<key prefix>"` returns nothing after history cleanup.
- [ ] A secret scanner (e.g. gitleaks: `gitleaks detect --source . --log-opts="--all"`) reports zero findings.
- [ ] Forks/other places checked; unresolved ones are listed with an owner.

## 4. Root cause (5 Whys)
1. Why was the secret published? It was in a file inside the repo.
2. Why was it in the repo? The config mixed secrets with non-secret settings and wasn't git-ignored.
3. Why wasn't it caught? No pre-commit or CI secret scanning, no push protection.
4. Why was a long-lived, broad credential in a dev's hands? No secret manager / short-lived credentials / least-privilege policy.
5. Why did process allow it? No secrets-handling guideline or onboarding training; no review gate on config files.

## 5. Preventive recommendations
| Layer | Control |
|---|---|
| Don't have secrets in code | Load secrets from environment variables or a secret manager (e.g. Vault, cloud secret managers). Commit only a `config.example` with placeholders. |
| Stop commits | `.gitignore` for `.env`/config files; **pre-commit hook** with gitleaks or similar. |
| Stop pushes | Enable the host's **secret scanning + push protection**; CI job that fails the build on detected secrets. |
| Limit damage | Least-privilege keys scoped to one service, **short-lived** tokens, IP restrictions, expiry, billing/usage alerts. |
| Detect fast | Alerts on anomalous key use; regular rotation. |
| People | Short training and a one-page "I leaked a secret, what now?" runbook (step 1 = rotate). |

## 6. Demo (evidence)
`demo/demo.sh` creates a local throwaway repo with a **fake** key (AWS's published example key), commits it, deletes it, and shows it is still recoverable from history and findable by a simple scanner-style regex; then removes it with `git filter-repo`. Output: `demo/demo_output.txt`. Nothing is pushed anywhere.

## 7. Assumptions and limits
- I assumed the credential is a cloud/API key with write access; if it were read-only or already expired, impact would be lower but the steps would be the same.
- I can't know if it was copied. The plan is built so that doesn't matter (rotation).
- Provider-specific log names differ (e.g. AWS CloudTrail, GitHub audit log); a real response would use the actual provider's tools.

## 8. References (open and check each before submitting)
- GitHub Docs — *Removing sensitive data from a repository*
- GitHub Docs — *About secret scanning* / *push protection*
- OWASP — *Secrets Management Cheat Sheet*
- NIST SP 800-61 — *Computer Security Incident Handling Guide*
- gitleaks (open-source secret scanner) — github.com/gitleaks/gitleaks
- git-filter-repo — github.com/newren/git-filter-repo

## 9. Screenshot
![Task 22 demo output](screenshots/task22-demo-1.png)
