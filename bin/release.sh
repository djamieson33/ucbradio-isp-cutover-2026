#!/bin/bash
# release.sh: Automate project version bump and changelog for releases
# Usage: ./bin/release.sh <major|minor|patch> "Description of release"

set -e

if [ $# -lt 2 ]; then
  echo "Usage: $0 <major|minor|patch> \"Description of release\""
  exit 1
fi

RELEASE_TYPE=$1
DESCRIPTION=$2

# Extract current version from README.md
CURRENT_VERSION=$(grep -Eo '\*\*Version:\*\* [0-9]+\.[0-9]+\.[0-9]+' README.md | awk '{print $2}')
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

case $RELEASE_TYPE in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Invalid release type: $RELEASE_TYPE. Use major, minor, or patch."
    exit 1
    ;;
esac

NEW_VERSION="$MAJOR.$MINOR.$PATCH"
DATE=$(date -u +%Y-%m-%d)

# Update README.md
sed -i '' -E "s/(\*\*Version:\*\*) [0-9]+\.[0-9]+\.[0-9]+/\1 $NEW_VERSION/" README.md
sed -i '' -E "s/(\*\*Last updated:\*\*) [0-9\-]+/\1 $DATE/" README.md

# Prepend to CHANGELOG.md
TMPFILE=$(mktemp)
echo -e "## [$NEW_VERSION] - $DATE\n- $DESCRIPTION\n" | cat - CHANGELOG.md > $TMPFILE && mv $TMPFILE CHANGELOG.md

echo "Release $NEW_VERSION created with description: $DESCRIPTION"

# Create a git tag for the new version
git add README.md CHANGELOG.md
git commit -m "Release $NEW_VERSION: $DESCRIPTION"
git tag -a "v$NEW_VERSION" -m "$DESCRIPTION"

echo "Git tag v$NEW_VERSION created. Pushing to remote..."
git push && git push --tags

# Create GitHub release using gh CLI
REPO=$(git config --get remote.origin.url | sed -E 's/git@github.com:(.*)\.git/\1/')
if command -v gh >/dev/null 2>&1; then
  gh release create "v$NEW_VERSION" --repo "$REPO" --title "v$NEW_VERSION" --notes "$DESCRIPTION"
  echo "GitHub release v$NEW_VERSION created."
else
  echo "gh CLI not found. Please install GitHub CLI to automate GitHub releases."
fi
