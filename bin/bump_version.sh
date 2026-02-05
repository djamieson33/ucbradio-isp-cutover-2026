#!/bin/bash
# bump_version.sh: Bump project version in README.md and CHANGELOG.md
# Usage: ./bin/bump_version.sh <new_version>

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <new_version>"
  exit 1
fi

NEW_VERSION="$1"
DATE=$(date -u +%Y-%m-%d)

# Update README.md
sed -i '' -E "s/(\*\*Version:\*\*) [0-9]+\.[0-9]+\.[0-9]+/\1 $NEW_VERSION/" README.md
sed -i '' -E "s/(\*\*Last updated:\*\*) [0-9\-]+/\1 $DATE/" README.md

# Prepend to CHANGELOG.md
TMPFILE=$(mktemp)
echo -e "## [$NEW_VERSION] - $DATE\n- Version bump to $NEW_VERSION.\n" | cat - CHANGELOG.md > $TMPFILE && mv $TMPFILE CHANGELOG.md

echo "Version updated to $NEW_VERSION in README.md and CHANGELOG.md."
