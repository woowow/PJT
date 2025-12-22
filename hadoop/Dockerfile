FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Hadoop + Java 버전
ENV HADOOP_VERSION=3.3.5
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV HADOOP_HOME=/usr/local/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# 기본 패키지 + Python3 포함
RUN apt-get update && \
    apt-get install -y \
        openjdk-11-jdk \
        ssh \
        curl \
        rsync \
        nano \
        python3 \
        python3-pip \
        python3-distutils \
        python3-venv \
    && apt-get clean

# python3 → python 심볼릭 링크 (Hadoop Streaming 호환용)
RUN ln -s /usr/bin/python3 /usr/bin/python || true

# Hadoop 다운로드 및 설치
RUN curl -O https://downloads.apache.org/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz && \
    tar -xzvf hadoop-$HADOOP_VERSION.tar.gz -C /usr/local && \
    mv /usr/local/hadoop-$HADOOP_VERSION $HADOOP_HOME && \
    rm hadoop-$HADOOP_VERSION.tar.gz

# Hadoop 설정 파일 복사
COPY core-site.xml $HADOOP_HOME/etc/hadoop/core-site.xml
COPY hdfs-site.xml $HADOOP_HOME/etc/hadoop/hdfs-site.xml
COPY yarn-site.xml $HADOOP_HOME/etc/hadoop/yarn-site.xml
COPY mapred-site.xml $HADOOP_HOME/etc/hadoop/mapred-site.xml
COPY capacity-scheduler.xml $HADOOP_HOME/etc/hadoop/capacity-scheduler.xml

# Entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 필요한 포트 공개
EXPOSE 9870 9864 9866 8088 8042 9000

CMD ["/entrypoint.sh"]
