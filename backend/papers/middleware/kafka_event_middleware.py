import json
import re
import logging
from django.utils.deprecation import MiddlewareMixin
from papers.services.kafka_producer import publish_user_event

logger = logging.getLogger(__name__)

TRACK_RE = re.compile(r"^/api/papers/(?P<paper_id>\d+)/track/?$")


class KafkaEventMiddleware(MiddlewareMixin):
    """
    특정 API가 2xx 성공했을 때 Kafka 이벤트 발행(제출용 최소)
    - POST /api/papers/<paper_id>/track/  -> VIEW_DETAIL
    - POST /api/favorites/toggle/        -> TOGGLE_FAVORITE
    """

    def process_response(self, request, response):
        try:
            if request.method != "POST":
                return response
            if not (200 <= response.status_code < 300):
                return response

            path = request.path.rstrip("/")

            # track
            m = TRACK_RE.match(request.path)
            if m:
                paper_id = int(m.group("paper_id"))
                body = self._safe_json_body(request)
                guest_id = body.get("guest_id")
                if guest_id is not None:
                    ok = publish_user_event(int(guest_id), paper_id, "VIEW_DETAIL", meta={"path": request.path})
                    logger.warning("[KafkaEventMiddleware] track published=%s guest_id=%s paper_id=%s",
                                   ok, guest_id, paper_id)
                return response

            # favorite toggle
            if path == "/api/favorites/toggle":
                body = self._safe_json_body(request)
                guest_id = body.get("guest_id")
                paper_id = body.get("paper_id")
                if guest_id is not None and paper_id is not None:
                    ok = publish_user_event(int(guest_id), int(paper_id), "TOGGLE_FAVORITE", meta={"path": request.path})
                    logger.warning("[KafkaEventMiddleware] favorite published=%s guest_id=%s paper_id=%s",
                                   ok, guest_id, paper_id)
                return response

            return response

        except Exception as e:
            logger.exception("[KafkaEventMiddleware] error: %s", str(e))
            return response

    @staticmethod
    def _safe_json_body(request):
        try:
            if not request.body:
                return {}
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
