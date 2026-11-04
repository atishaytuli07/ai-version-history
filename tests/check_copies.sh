#!/usr/bin/env bash
# The GitHub layer ships in three places; they must stay identical.
set -euo pipefail
cd "$(dirname "$0")/.."
G=skills/versioning-ai-work/assets/github-layer
fail=0
same() { cmp -s "$1" "$2" || { echo "Out of sync: $1 vs $2"; fail=1; }; }
for dir in github-layer/copy-paste lovable-kit/pro/copy-paste; do
  same "$dir/1-pending.json"    "$G/ai-versions/pending.json"
  same "$dir/2-ai-version.mjs"  "$G/github/scripts/ai-version.mjs"
  same "$dir/3-ai-restore.mjs"  "$G/github/scripts/ai-restore.mjs"
  same "$dir/4-ai-restore.yml"  "$G/github/workflows/ai-restore.yml"
  same "$dir/5-VersionPill.tsx" "$G/pill/VersionPill.tsx"
  same "$dir/6-ai-versions.yml" "$G/github/workflows/ai-versions.yml"
done
same github-layer/RULES.md skills/versioning-ai-work/assets/rules/github-layer-rules.md
[ $fail = 0 ] && echo "All copies match."
exit $fail
