#!/bin/bash
set -e

export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

service ssh start

echo "[$HOSTNAME] Starting Hadoop Services..."

NAMENODE_DIR="$HADOOP_HOME/hdfs/namenode"
DATANODE_DIR="$HADOOP_HOME/hdfs/datanode"

if [[ "$HOSTNAME" == "namenode" ]]; then
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
