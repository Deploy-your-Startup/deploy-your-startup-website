#!/bin/bash
# Propose an installer pin as a pull request; main only changes through reviewed PRs.
#   cli_release_pr.sh pending <tag>  prints pending=true when its PR is already open
#   cli_release_pr.sh open <tag>     commits the pin on release/cli-<tag> and opens the PR
set -euo pipefail

action="${1:-}"
tag="${2:-}"
if ! [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: cli_release_pr.sh pending|open vX.Y.Z" >&2
  exit 1
fi
branch="release/cli-$tag"

case "$action" in
  pending)
    # Scheduled runs repeat every ten minutes; an open PR means nothing to redo.
    open="$(gh pr list --head "$branch" --state open --json number --jq length)"
    if [ "$open" = 0 ]; then echo "pending=false"; else echo "pending=true"; fi
    ;;
  open)
    git switch -c "$branch"
    git add frontend/public/install.sh
    git commit -m "chore: update installer to CLI $tag"
    git push --force origin "$branch"
    gh pr create --base main --head "$branch" \
      --title "chore: update installer to CLI $tag" \
      --body "Advances the installer pin to [CLI $tag](https://github.com/Deploy-your-Startup/cli/releases/tag/$tag). The website tests passed with this pin before the PR was opened. Merging deploys it."
    # A newer release replaces older pin proposals.
    gh pr list --state open --json number,headRefName \
      --jq ".[] | select(.headRefName | startswith(\"release/cli-\")) | select(.headRefName != \"$branch\") | .number" |
      while read -r number; do
        gh pr close "$number" --comment "Superseded by $tag." --delete-branch
      done
    # Pull requests opened with the workflow token start no pull_request runs;
    # run the required checks on the branch instead.
    gh workflow run deploy.yml --ref "$branch"
    ;;
  *)
    echo "Usage: cli_release_pr.sh pending|open vX.Y.Z" >&2
    exit 1
    ;;
esac
