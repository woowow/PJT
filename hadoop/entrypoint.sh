#!/bin/bash

# Java/Hadoop 환경 변수 설정
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export HADOOP_HOME=/usr/local/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

service ssh start

echo "[$HOSTNAME] Starting Hadoop Services..."

if [[ "$HOSTNAME" == "namenode" ]]; then
    echo "[Namenode] Formatting HDFS..."
    hdfs namenode -format -force

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
