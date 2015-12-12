#!/bin/sh

set -e

if [ -n "$1" ]; then
  cd "$1"
fi

for x in *.txt; do
  if [ ! -f "${x}" ]; then
    break
  fi

  name=$(basename ${x})
  tmp=$(basename ${x}).new

  echo "Updating ${name}..."
  if curl -sS http://celestrak.com/NORAD/elements/${name} > ${tmp}; then
    mv ${tmp} ${name}
  fi
done

