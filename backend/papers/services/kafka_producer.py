import json
import uuid
import logging
from datetime import datetime, timezone
from django.conf import settings

try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

logger = logging.getLogger(__name__)
_producer = None


def _enabled() -> bool:
    return bool(getattr(settings, "USE_KAFKA", False)) and KafkaProducer is not None


def get_producer():
    """
    최대한 단순/확실 버전:
    - acks/timeouts/linger 같은 튜닝값 제거 (여기서 자주 삑남)
    - 실패하면 None 반환 + 로그
    """
    global _producer
    if not _enabled():
        return None

    if _producer is not None:
        return _producer

    bootstrap = getattr(settings, "KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    try:
        _producer = KafkaProducer(
            bootstrap_servers=[s.strip() for s in bootstrap.split(",") if s.strip()],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda v: str(v).encode("utf-8"),
            acks=1,          # ✅ int 로
            retries=3,
        )
        print(f"[KafkaProducer] initialized bootstrap={bootstrap}")
    except Exception as e:
        _producer = None
        print(f"[KafkaProducer] init failed: {e}")

    return _producer


def publish_user_event(guest_id: int, paper_id: int, action: str, meta: dict | None = None) -> bool:
    """
    - send + flush(5)로 '진짜 브로커에 들어갔는지' 확실히 함
    - 실패해도 False 반환
    """
    if not _enabled():
        print("[KafkaProducer] disabled (USE_KAFKA false or kafka-python missing)")
        return False

    producer = get_producer()
    if producer is None:
        return False

    topic = getattr(settings, "KAFKA_TOPIC_EVENTS", "paper.events.v1")

    payload = {
        "event_id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "guest_id": int(guest_id),
        "paper_id": int(paper_id),
        "action": str(action),
        "meta": meta or {},
    }

    try:
        producer.send(topic, key=str(guest_id), value=payload)
        producer.flush(5)  # ✅ 여기서 확실히 기록되도록
        print(f"[KafkaProducer] sent topic={topic} guest_id={guest_id} paper_id={paper_id} action={action}")
        return True
    except Exception as e:
        print(f"[KafkaProducer] send failed: {e}")
        return False
