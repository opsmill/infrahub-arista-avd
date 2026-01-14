#!/bin/bash
# Regenerate AVD hostvars for all devices in the fabric

BRANCH="${1:-fabric-a}"

HOSTNAMES=(
  ss-fabric-a-1
  ss-fabric-a-2
  ss-fabric-a-3
  ss-fabric-a-4
  ss-fabric-a-5
  ss-fabric-a-6
  spine-pod-a2-1
  spine-pod-a3-1
  spine-pod-a2-2
  spine-pod-a3-2
  spine-pod-a2-3
  spine-pod-a3-3
  spine-pod-a2-4
  spine-pod-a3-4
  leaf-pod-a2-1-1
  leaf-pod-a3-1-1
  leaf-pod-a3-3-1
  leaf-pod-a3-1-2
  leaf-pod-a2-4-1
  leaf-pod-a2-3-1
  leaf-pod-a3-2-1
  leaf-pod-a2-3-2
  leaf-pod-a3-4-1
  leaf-pod-a2-1-2
  leaf-pod-a2-2-1
)

echo "Regenerating hostvars for ${#HOSTNAMES[@]} devices on branch: $BRANCH"
echo ""

for hostname in "${HOSTNAMES[@]}"; do
  echo "=== $hostname ==="
  uv run infrahubctl generator generate-avd-device-hostvar hostname=$hostname --branch "$BRANCH"
  echo ""
done

echo "Done!"
