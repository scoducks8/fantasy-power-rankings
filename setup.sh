#!/bin/bash
# One-time setup for the fantasy power rankings repo.
# Run in Terminal:
#     bash ~/Documents/Claude/fantasy-power-rankings/setup.sh
#
# Terminal has full permissions, so the file-deletion limit that blocks
# Claude inside this folder does not apply to you.

set -u

GH_USER="scoducks8"
REPO="fantasy-power-rankings"

cd "$HOME/Documents/Claude/$REPO" || {
  echo "Can't find ~/Documents/Claude/$REPO"
  exit 1
}

echo "==> Clearing the stale git locks"
rm -f .git/HEAD.lock .git/ORIG_HEAD.lock .git/index.lock \
      .git/refs/heads/main.lock .git/objects/maintenance.lock .probe
find .git/objects -name 'tmp_obj_*' -delete 2>/dev/null
rm -rf _to_delete
git reset -q
echo "    done"

echo
echo "==> Local commits"
git log --oneline | head -3

echo
echo "==> SSH key for GitHub"
# SSH rather than a token: nothing secret is ever pasted into a command,
# and it doesn't expire.
if [ -f "$HOME/.ssh/id_ed25519.pub" ]; then
  echo "    Reusing your existing key."
else
  ssh-keygen -t ed25519 -C "bentesluk@gmail.com" -f "$HOME/.ssh/id_ed25519" -N ""
  echo "    Created ~/.ssh/id_ed25519"
fi

echo
echo "======================================================================"
echo " COPY THE LINE BELOW - this is your PUBLIC key, safe to share."
echo "======================================================================"
echo
cat "$HOME/.ssh/id_ed25519.pub"
echo
echo "======================================================================"
echo
echo "Paste it here:  https://github.com/settings/ssh/new"
echo "  Title: MacBook Air     Key: the line above     -> Add SSH key"
echo
read -r -p "Press Return once the key is added... " _

echo
echo "==> Testing the connection"
ssh-keyscan -t ed25519 github.com >> "$HOME/.ssh/known_hosts" 2>/dev/null
ssh -o StrictHostKeyChecking=no -T git@github.com 2>&1 | head -2

echo
echo "======================================================================"
echo " HEADS UP"
echo "======================================================================"
echo "Your GitHub repo currently holds one commit: a starter README.md with"
echo "the description \"d\". Your local repo has the real project but a"
echo "separate history, so a normal push will be rejected."
echo
echo "This script will FORCE PUSH, which replaces that starter README with"
echo "the real project. Nothing you care about is lost - but if you added"
echo "anything to the repo on github.com since creating it, stop now."
echo
read -r -p "Type yes to overwrite the remote: " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "Stopped. Nothing pushed."
  exit 0
fi

echo
echo "==> Pushing"
git remote remove origin 2>/dev/null
git remote add origin "git@github.com:${GH_USER}/${REPO}.git"
git branch -M main

if git push -u origin main --force; then
  cat <<EOF

======================================================================
 PUSHED. Two things left - the second one only you can do.
======================================================================

1. Turn on Pages:
   https://github.com/${GH_USER}/${REPO}/settings/pages
   Source: Deploy from a branch
   Branch: main    Folder: /docs    -> Save

2. Add your two ESPN cookies as secrets:
   https://github.com/${GH_USER}/${REPO}/settings/secrets/actions
   New repository secret -> ESPN_S2    = your espn_s2 cookie value
   New repository secret -> ESPN_SWID  = your SWID value, braces included

   Get them from Chrome while logged in to fantasy.espn.com:
   DevTools (Cmd+Option+I) -> Application -> Cookies -> fantasy.espn.com

   LEAGUE_ID and SEASON are already set as repository variables.

Your site will be at:
   https://${GH_USER}.github.io/${REPO}/

EOF
else
  echo
  echo "Push failed. Check the key is registered:  ssh -T git@github.com"
  echo "You should see: 'Hi ${GH_USER}! You've successfully authenticated'"
fi
