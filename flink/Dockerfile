# ---------- build stage ----------
FROM maven:3.9.6-eclipse-temurin-11 AS builder
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package

# ---------- runtime stage ----------
FROM flink:1.18.1-scala_2.12-java11
WORKDIR /opt/flink

RUN mkdir -p /opt/flink/usrlib
COPY --from=builder /build/target/paper-flink-job.jar /opt/flink/usrlib/paper-flink-job.jar
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
