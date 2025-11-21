# import json
# from kafka import KafkaProducer

# _producer = None

# def get_producer():
#     global _producer
#     if _producer is None:
#         try:
#             _producer = KafkaProducer(
#                 bootstrap_servers=['localhost:9092'],
#                 value_serializer=lambda v: json.dumps(v).encode('utf-8')
#             )
#         except Exception as e:
#             print("[Kafka disabled] Producer init failed:", e)
#             _producer = None
#     return _producer

# def publish_paper_event(paper):
#     producer = get_producer()
#     if producer is None:
#         return

#     try:
#         producer.send("new_paper", {
#             "id": paper.id,
#             "title": paper.title
#         })
#     except Exception as e:
#         print("[Kafka publish failed]:", e)

# papers/services/kafka_producer.py
import json
from django.conf import settings

# Kafka 모듈 로드만, 실제 producer는 필요할 때만 초기화
try:
    from kafka import KafkaProducer
except ImportError:
    KafkaProducer = None

_producer = None

def get_producer():
    if not getattr(settings, "USE_KAFKA", False):
        return None

    global _producer
    if _producer is None and KafkaProducer is not None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            print("[Kafka disabled] Producer init failed:", e)
            _producer = None

    return _producer


def publish_paper_event(paper):
    if not getattr(settings, "USE_KAFKA", False):
        return  # 완전 비활성화
    
    producer = get_producer()
    if producer is None:
        return

    try:
        producer.send("new_paper", {
            "id": paper.id,
            "title": paper.title
        })
    except Exception as e:
        print("[Kafka publish failed]:", e)
