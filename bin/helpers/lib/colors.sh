# colors.sh - Shared color output functions for shell scripts

# Color codes
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

# Print green 'OK' message
function green_ok() {
    echo -e "${GREEN}✔ $1${NC}"
}

# Print red 'Error' message
function red_error() {
    echo -e "${RED}✖ $1${NC}"
}

# Print yellow 'Warning' message
function yellow_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}
