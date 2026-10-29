#!/usr/bin/env bash
# Safe demo: FAKE key (AWS's documented example key), local repo only, nothing is pushed anywhere.
set -e
rm -rf /tmp/leak-demo && mkdir /tmp/leak-demo && cd /tmp/leak-demo
git init -q && git config user.email "dev@example.com" && git config user.name "Dev" && git config core.autocrlf false

echo "### STEP 1: developer commits config with a (FAKE) credential"
printf 'DB_HOST=localhost\nAWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n' > config.env
git add config.env && git commit -qm "add config"

echo; echo "### STEP 2: 5 minutes later developer deletes the file"
git rm -q config.env && git commit -qm "remove config"

echo; echo "### STEP 3: file is gone from the working tree..."
ls -la | grep config.env || echo "(config.env not in working tree)"

echo; echo "### STEP 4: ...but the secret is still in history"
git log --all --oneline
echo "--- searching all history for the key pattern ---"
git log --all -p -S"AKIA" --oneline | grep -E "^[0-9a-f]{7}|AKIA|SECRET"

echo; echo "### STEP 5: scanner-style regex over every commit (what bots do)"
for c in $(git rev-list --all); do git grep -nE 'AKIA[0-9A-Z]{16}' "$c" 2>/dev/null | sed "s/^/commit ${c:0:7}: /"; done

echo; echo "### STEP 6: cleanup history (after the key is ROTATED) with git-filter-repo"
if command -v git-filter-repo >/dev/null 2>&1; then
  git filter-repo --invert-paths --path config.env --force >/dev/null 2>&1
  echo "after filter-repo:"; git log --all -p -S"AKIA" --oneline | grep -c AKIA || true
else
  echo "(git-filter-repo not installed here; on your PC: pip install git-filter-repo, then: git filter-repo --invert-paths --path config.env --force)"
fi
