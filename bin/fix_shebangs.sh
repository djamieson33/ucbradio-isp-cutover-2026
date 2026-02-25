#!/usr/bin/env bash
set -euo pipefail

# UCB Radio – Repo Utility
# Tool: fix_shebangs
# Purpose:
#   Ensure Python executable scripts in bin/ have the shebang
#   '#!/usr/bin/env python3' as the first line.
#
#   If a file starts with a '# bin/...' header comment above
#   the shebang, it will be moved below the shebang.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT_DIR/bin"

echo "[INFO] Scanning $BIN_DIR for Python scripts..."

fix_file() {
  local file="$1"

  # Only operate on files that contain a python shebang somewhere
  if ! grep -q '^#!.*python' "$file"; then
    return
  fi

  # Read file
  mapfile -t lines < "$file"

  # Find shebang line
  local shebang_index=-1
  for i in "${!lines[@]}"; do
    if [[ "${lines[$i]}" =~ ^#!.*python ]]; then
      shebang_index=$i
      break
    fi
  done

  if [[ $shebang_index -lt 0 ]]; then
    return
  fi

  # If shebang already first line and correct, skip
  if [[ $shebang_index -eq 0 ]] && [[ "${lines[0]}" == "#!/usr/bin/env python3" ]]; then
    return
  fi

  echo "[FIX] $file"

  # Extract shebang
  local shebang="${lines[$shebang_index]}"

  # Remove shebang from its current location
  unset 'lines[$shebang_index]'

  # Rebuild file:
  # 1) correct shebang
  # 2) any leading "# bin/..." header lines
  # 3) rest of file

  new_lines=()
  new_lines+=("#!/usr/bin/env python3")

  # Preserve label line if present at top
  for line in "${lines[@]}"; do
    if [[ "$line" =~ ^#\ bin/ ]]; then
      new_lines+=("$line")
    fi
  done

  for line in "${lines[@]}"; do
    if [[ ! "$line" =~ ^#\ bin/ ]]; then
      new_lines+=("$line")
    fi
  done

  printf "%s\n" "${new_lines[@]}" > "$file"
  chmod +x "$file"
}

export -f fix_file

find "$BIN_DIR" -type f -name "*.py" -exec bash -c 'fix_file "$0"' {} \;

echo "[DONE] Shebang normalization complete."
