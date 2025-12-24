FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

ENV HADOOP_VERSION=3.3.5
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV HADOOP_HOME=/usr/local/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

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

RUN ln -s /usr/bin/python3 /usr/bin/python || true

RUN curl -O https://downloads.apache.org/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz && \
    tar -xzvf hadoop-$HADOOP_VERSION.tar.gz -C /usr/local && \
    mv /usr/local/hadoop-$HADOOP_VERSION $HADOOP_HOME && \
    rm hadoop-$HADOOP_VERSION.tar.gz

COPY core-site.xml $HADOOP_HOME/etc/hadoop/core-site.xml
COPY hdfs-site.xml $HADOOP_HOME/etc/hadoop/hdfs-site.xml
COPY yarn-site.xml $HADOOP_HOME/etc/hadoop/yarn-site.xml
COPY mapred-site.xml $HADOOP_HOME/etc/hadoop/mapred-site.xml
COPY capacity-scheduler.xml $HADOOP_HOME/etc/hadoop/capacity-scheduler.xml

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 9870 9864 9866 8088 8042 9000

CMD ["/entrypoint.sh"]
