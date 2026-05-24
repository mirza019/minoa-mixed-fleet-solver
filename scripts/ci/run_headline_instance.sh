#!/usr/bin/env bash
set -euo pipefail

instance="${1:?Usage: run_headline_instance.sh small|medium|large}"

case "$instance" in
  small)
    input="data/raw/minoa/senior/Small_Input_S.json"
    output="outputs/minoa/ci/Small_Output_ci.json"
    variants=8
    iterations=64
    seed=19
    limit=240
    ;;
  medium)
    input="data/raw/minoa/senior/Medium_Input_S.json"
    output="outputs/minoa/ci/Medium_Output_ci.json"
    variants=8
    iterations=48
    seed=103
    limit=420
    ;;
  large)
    input="data/raw/minoa/senior/Large_Input_S.json"
    output="outputs/minoa/ci/Large_Output_ci.json"
    variants=8
    iterations=24
    seed=23
    limit=900
    ;;
  *)
    echo "Unknown instance: $instance" >&2
    exit 2
    ;;
esac

mkdir -p outputs/minoa/ci

export MINOA_DEPOT_BRIDGE_MIN_GAP="${MINOA_DEPOT_BRIDGE_MIN_GAP:-999999}"

echo "Running optimized MINOA solver for $instance"
.venv/bin/python scripts/minoa_optimize.py "$input" \
  --output "$output" \
  --variants "$variants" \
  --per-direction \
  --local-iterations "$iterations" \
  --seed "$seed" \
  --builder pathcover-cost \
  --ev-mode charging \
  --time-limit "$limit" \
  | tee "outputs/minoa/ci/${instance}_search.log"

if [[ ! -s "$output" ]]; then
  echo "No valid output was produced for $instance" >&2
  exit 1
fi

echo "Validator/report table for $instance"
.venv/bin/python scripts/minoa_report.py "$input:$output" \
  | tee "outputs/minoa/ci/${instance}_report.md"
