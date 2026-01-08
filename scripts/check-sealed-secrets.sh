#!/bin/bash
# Checks if sealed-settings.yaml is older than settings.yaml

ERROR=0

# Find all settings.yaml files in .k8s directory
while IFS= read -r setting_file; do
  dir=$(dirname "$setting_file")
  sealed_file="$dir/sealed-settings.yaml"

  if [ -f "$sealed_file" ]; then
    # Check if settings.yaml is newer than sealed-settings.yaml
    if [ "$setting_file" -nt "$sealed_file" ]; then
      echo "❌ Error: Secrets out of sync in $dir"
      echo "   'settings.yaml' is newer than 'sealed-settings.yaml'."
      echo "   👉 Please run: make seal env=$(basename $dir)"
      ERROR=1
    fi
  fi
done < <(find .k8s -name "settings.yaml")

if [ $ERROR -eq 1 ]; then
  exit 1
fi

echo "✅ All sealed secrets are up to date."
exit 0
