#!/usr/bin/env bash
set -euo pipefail

JOBMANAGER_HOST="${JOBMANAGER_HOST:-flink-jobmanager}"
JOBMANAGER_PORT="${JOBMANAGER_PORT:-8081}"
JAR_PATH="${JAR_PATH:-/opt/flink/usrlib/paper-flink-job.jar}"
MAIN_CLASS="${MAIN_CLASS:-com.paper.flink.UserEventAggJob}"

echo "[entrypoint] waiting for Flink JobManager REST..."
until curl -sf "http://${JOBMANAGER_HOST}:${JOBMANAGER_PORT}/overview" >/dev/null; do
  sleep 2
done
echo "[entrypoint] JobManager is up."

echo "[entrypoint] submitting job..."
/opt/flink/bin/flink run -d \
  -m "${JOBMANAGER_HOST}:${JOBMANAGER_PORT}" \
  -c "${MAIN_CLASS}" \
  "${JAR_PATH}"

echo "[entrypoint] job submitted. keep container alive for logs."
tail -f /dev/null
