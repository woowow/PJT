#!/bin/bash

# Java/Hadoop 환경 변수 설정
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# ✅ sshd가 있을 때만 실행 (없으면 스킵)
if command -v sshd >/dev/null 2>&1; then
  mkdir -p /run/sshd
  /usr/sbin/sshd || true
else
  echo "[$HOSTNAME] sshd not found. skip ssh start."
fi

echo "[$HOSTNAME] Starting Hadoop Services..."

NAMENODE_DIR="$HADOOP_HOME/hdfs/namenode"

if [[ "$HOSTNAME" == "namenode" ]]; then
    # ✅ 이미 포맷되어 있으면 포맷 생략
    if [[ -d "$NAMENODE_DIR/current" ]]; then
        echo "[Namenode] HDFS already formatted. Skip format."
    else
        echo "[Namenode] Formatting HDFS (first time only)..."
        hdfs namenode -format -force
    fi

    echo "[Namenode] Starting NameNode..."
    hdfs namenode &

    echo "[Namenode] Starting ResourceManager..."
    yarn resourcemanager &

    tail -f /dev/null
else
    echo "[$HOSTNAME] Starting DataNode..."
    hdfs datanode &

    echo "[$HOSTNAME] Starting NodeManager..."
    yarn nodemanager &

    tail -f /dev/null
fi
