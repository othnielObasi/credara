#!/usr/bin/env bash
# Ensure Docker daemon is running in cloud/workspace environments.
set -euo pipefail

resolve_docker() {
  if docker info >/dev/null 2>&1; then
    echo docker
    return 0
  fi
  if sudo docker info >/dev/null 2>&1; then
    echo "sudo docker"
    return 0
  fi
  return 1
}

if ! resolve_docker >/dev/null 2>&1; then
  if command -v dockerd >/dev/null 2>&1; then
    echo "Starting Docker daemon..."
    sudo mkdir -p /etc/docker
    if [[ ! -f /etc/docker/daemon.json ]]; then
      echo '{"storage-driver":"vfs"}' | sudo tee /etc/docker/daemon.json >/dev/null
    fi
    sudo nohup dockerd >/tmp/dockerd.log 2>&1 &
    for _ in $(seq 1 30); do
      if resolve_docker >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  fi
fi

if ! DOCKER=$(resolve_docker); then
  echo "Docker is not available."
  echo "Run: make docker-setup"
  [[ -f /tmp/dockerd.log ]] && tail -5 /tmp/dockerd.log
  exit 1
fi

export DOCKER
echo "Using: $DOCKER"
