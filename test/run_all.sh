#!/bin/bash

set -o xtrace

mkdir output

exit_code=0

for file in ./[0-9]*.*.py
do
  python3 "$file" auto || exit_code=1
done

python3 output_diff.py && exit "$exit_code"