#!/usr/bin/env bash
# Apply GitHub repository topics and description (requires: gh auth login)
set -euo pipefail

REPO="${1:-chaffybird56/BatteryPack}"

TOPICS=(
  battery-simulation
  lithium-ion
  battery-pack
  battery-modeling
  equivalent-circuit-model
  electro-thermal
  bms
  thermal-runaway
  state-of-charge
  round-trip-efficiency
  drive-cycle
  fast-charging
  electric-vehicle
  energy-storage
  grid-storage
  ups-backup
  monte-carlo
  python
  open-source
  simulation
)

DESC="Python battery pack simulator: ECM electro-thermal model, RTE, BMS, thermal runaway, drive cycles, EV/grid/UPS analysis."

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: https://cli.github.com/"
  exit 1
fi

gh auth status >/dev/null 2>&1 || {
  echo "Run: gh auth login"
  exit 1
}

ARGS=()
for t in "${TOPICS[@]}"; do
  ARGS+=(--add-topic "$t")
done

gh repo edit "$REPO" --description "$DESC" "${ARGS[@]}"
echo "Updated $REPO description and ${#TOPICS[@]} topics."
