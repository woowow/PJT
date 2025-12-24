import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, to_timestamp, to_date, date_format
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, MapType

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "paper.events.v1")

HDFS_BASE = os.getenv("HDFS_BASE", "hdfs://namenode:9000")
HDFS_OUT = os.getenv("HDFS_OUT", f"{HDFS_BASE}/data/events/paper_events")
CHECKPOINT = os.getenv("CHECKPOINT", f"{HDFS_BASE}/data/checkpoints/paper_events")

schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("ts", StringType(), True),          # ISO string
    StructField("guest_id", IntegerType(), True),
    StructField("paper_id", IntegerType(), True),
    StructField("action", StringType(), True),
    StructField("meta", MapType(StringType(), StringType()), True),
])

def main():
    spark = (
        SparkSession.builder
        .appName("kafka-to-hdfs-paper-events")
        # 로컬 테스트 편의 (운영이면 제거 가능)
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "latest")
        .load()
    )

    # kafka value(bytes) -> string
    value_df = raw.selectExpr("CAST(value AS STRING) AS json_str")

    parsed = value_df.select(from_json(col("json_str"), schema).alias("e")).select("e.*")

    # ts -> timestamp 변환(파싱 실패해도 null)
    with_ts = parsed.withColumn("event_ts", to_timestamp(col("ts")))

    # 파티션 컬럼 생성 (event_ts가 null이면 dt/hour가 null -> 그 행은 별도 디렉토리에 쌓일 수 있음)
    out = (
        with_ts
        .withColumn("dt", to_date(col("event_ts")))
        .withColumn("hour", date_format(col("event_ts"), "HH"))
    )

    # Parquet 적재
    query = (
        out.writeStream
        .format("parquet")
        .option("path", HDFS_OUT)
        .option("checkpointLocation", CHECKPOINT)
        .partitionBy("dt", "hour")
        .outputMode("append")
        .start()
    )

    query.awaitTermination()

if __name__ == "__main__":
    main()
