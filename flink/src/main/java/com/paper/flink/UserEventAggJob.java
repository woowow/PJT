package com.paper.flink;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.connector.jdbc.JdbcConnectionOptions;
import org.apache.flink.connector.jdbc.JdbcExecutionOptions;
import org.apache.flink.connector.jdbc.JdbcSink;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.source.enumerator.initializer.OffsetsInitializer;
import org.apache.flink.streaming.api.datastream.DataStreamSource;
import org.apache.flink.streaming.api.datastream.SingleOutputStreamOperator;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.api.common.serialization.SimpleStringSchema;

import java.io.Serializable;
import java.util.Locale;
import java.util.Objects;

public class UserEventAggJob {

    // Jackson은 매 레코드마다 만들면 느리고 GC가 커져서 static 1개 사용
    private static final ObjectMapper MAPPER = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        final StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // 운영에서 최소한의 안정성: 체크포인트(원하면 끄기)
        env.enableCheckpointing(10_000);

        // ---- env vars ----
        final String brokers = getenv("KAFKA_BOOTSTRAP", "kafka:9092");
        final String topic = getenv("KAFKA_TOPIC", "paper.events.v1");
        final String groupId = getenv("KAFKA_GROUP_ID", "paper-flink-agg");

        final String jdbcUrl = getenv("JDBC_URL", "jdbc:postgresql://postgres:5432/paper_db");
        final String jdbcUser = getenv("JDBC_USER", "postgres");
        final String jdbcPassword = getenv("JDBC_PASSWORD", "postgres");

        // ---- Kafka Source ----
        KafkaSource<String> source = KafkaSource.<String>builder()
                .setBootstrapServers(brokers)
                .setTopics(topic)
                .setGroupId(groupId)
                .setStartingOffsets(OffsetsInitializer.latest())
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build();

        DataStreamSource<String> raw = env.fromSource(
                source,
                WatermarkStrategy.noWatermarks(),
                "kafka-paper-events"
        );

        // ---- Parse JSON -> UserEvent ----
        SingleOutputStreamOperator<UserEvent> events = raw
                .map(new ParseEvent())
                .name("parse-json")
                .filter(Objects::nonNull)
                .name("drop-null");

        // ---- Filter actions we count ----
        SingleOutputStreamOperator<UserEvent> inc = events
                .filter(UserEvent::isCountable)
                .name("filter-countable");

        // ---- JDBC Options ----
        JdbcExecutionOptions execOpts = JdbcExecutionOptions.builder()
                .withBatchSize(200)
                .withBatchIntervalMs(1000)
                .withMaxRetries(3)
                .build();

        JdbcConnectionOptions connOpts = new JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
                .withUrl(jdbcUrl)
                .withDriverName("org.postgresql.Driver")
                .withUsername(jdbcUser)
                .withPassword(jdbcPassword)
                .build();

        // 1) paper.weekly_count += 1
        inc.addSink(
                JdbcSink.sink(
                        "UPDATE paper SET weekly_count = weekly_count + 1 WHERE paper_id = ?",
                        (ps, e) -> ps.setInt(1, e.paperId),
                        execOpts,
                        connOpts
                )
        ).name("sink-paper-weekly");

        // 2) guestcategorycount upsert (+1) : paper.category_id를 서브쿼리로 가져옴
        // 주의: paper_id가 없으면 SELECT가 0행이라 아무 것도 안 들어감(안전)
        final String upsertSql =
                "INSERT INTO guestcategorycount (guest_id, category_id, count) " +
                "SELECT ?, p.category_id, 1 FROM paper p WHERE p.paper_id = ? " +
                "ON CONFLICT (guest_id, category_id) DO UPDATE " +
                "SET count = guestcategorycount.count + 1";

        inc.addSink(
                JdbcSink.sink(
                        upsertSql,
                        (ps, e) -> {
                            ps.setInt(1, e.guestId);
                            ps.setInt(2, e.paperId);
                        },
                        execOpts,
                        connOpts
                )
        ).name("sink-guestcategorycount");

        env.execute("paper-events-aggregation");
    }

    private static String getenv(String k, String def) {
        String v = System.getenv(k);
        return (v == null || v.isBlank()) ? def : v.trim();
    }

    // ----------------------------
    // Model
    // ----------------------------
    public static class UserEvent implements Serializable {
        public String eventId;
        public String ts;
        public int guestId;
        public int paperId;
        public String action;

        public boolean isCountable() {
            // 여기서 어떤 action을 "카운트"로 볼지 정의
            // 너의 백엔드가 쓰는 action: VIEW_DETAIL, FAVORITE_ADD, FAVORITE_REMOVE
            String a = (action == null) ? "" : action.toUpperCase(Locale.ROOT);
            return a.equals("VIEW_DETAIL") || a.equals("FAVORITE_ADD");
        }
    }

    // ----------------------------
    // Parser
    // ----------------------------
    public static class ParseEvent implements MapFunction<String, UserEvent> {
        @Override
        public UserEvent map(String value) {
            try {
                JsonNode n = MAPPER.readTree(value);

                JsonNode guest = n.get("guest_id");
                JsonNode paper = n.get("paper_id");
                JsonNode action = n.get("action");

                if (guest == null || paper == null || action == null) return null;
                if (!guest.canConvertToInt() || !paper.canConvertToInt()) return null;

                UserEvent e = new UserEvent();
                e.eventId = n.has("event_id") ? n.get("event_id").asText() : null;
                e.ts = n.has("ts") ? n.get("ts").asText() : null;
                e.guestId = guest.asInt();
                e.paperId = paper.asInt();
                e.action = action.asText();
                return e;
            } catch (Exception ex) {
                // JSON 깨짐/형식 불일치 => 그냥 버림 (잡이 죽지 않게)
                return null;
            }
        }
    }
}
