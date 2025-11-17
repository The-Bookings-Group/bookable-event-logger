import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, Union

from google.cloud import pubsub_v1
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class EventLogger:
    """
    EventLogger publishes structured JSON events to a Pub/Sub topic.
    Pub/Sub → BigQuery subscription inserts the event into BigQuery
    using the table schema.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        topic_name: Optional[str] = None,
        environment: Optional[str] = None,
        service_name: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        # Resolve config
        self.project_id = project_id or os.getenv("LOG_GCP_PROJECT")
        self.topic_name = topic_name or os.getenv("LOG_TOPIC", "events")
        self.environment = environment or os.getenv("LOG_ENVIRONMENT")
        self.service_name = service_name or os.getenv("LOG_SERVICE_NAME")
        self.credentials_path = credentials_path or os.getenv("LOG_GCP_CREDENTIALS")

        required = {
            "LOG_GCP_PROJECT / project_id": self.project_id,
            "LOG_TOPIC / topic_name": self.topic_name,
            "LOG_ENVIRONMENT / environment": self.environment,
            "LOG_SERVICE_NAME / service_name": self.service_name,
            "LOG_GCP_CREDENTIALS / credentials_path": self.credentials_path,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(
                "Missing required config for EventLogger: " + ", ".join(missing)
            )

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path
        )
        self.publisher = pubsub_v1.PublisherClient(credentials=credentials)
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)

        logger.debug(
            "EventLogger initialized for service=%s, environment=%s, topic=%s",
            self.service_name,
            self.environment,
            self.topic_path,
        )

    def _build_event(
        self,
        *,
        event_type: str,
        level: str,
        data: Dict[str, Any],
        service: Optional[str],
        correlation_id: Optional[str],
        actor: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        service_name = service or self.service_name
        actor_obj = actor or {}
        data_obj = data or {}

        event = {
            "event_id": str(uuid.uuid4()),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "service": service_name,
            "event_type": event_type,
            "level": level,
            "environment": self.environment,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            # `actor` and `data` are JSON-encoded strings
            "actor": json.dumps(actor_obj),
            "data": json.dumps(data_obj),
        }
        return event

    def log_event(
        self,
        *,
        event_type: str,
        level: str,
        data: Dict[str, Any],
        service: Optional[str] = None,
        correlation_id: Optional[str] = None,
        actor: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Optional[pubsub_v1.publisher.futures.Future]]:
        """Publish an event to Pub/Sub in the agreed schema."""
        event = self._build_event(
            event_type=event_type,
            level=level,
            data=data,
            service=service,
            correlation_id=correlation_id,
            actor=actor,
        )

        payload = json.dumps(event).encode("utf-8")
        logger.info("[EventLogger] %s %s - %s", event_type, level, event["event_id"])

        try:
            future = self.publisher.publish(self.topic_path, payload)
            logger.debug("Published event %s to %s", event["event_id"], self.topic_path)
            return event, future
        except Exception as e:  # noqa: BLE001
            logger.error("Failed to publish event to Pub/Sub: %s", e)
            return event, None

    def log(
        self,
        level: str,
        event_type: str,
        correlation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        """Generic dynamic-level log method."""
        return self.log_event(
            event_type=event_type,
            level=level,
            data=data or {},
            correlation_id=correlation_id,
            actor=actor,
            service=service,
        )

    def debug(
        self,
        event_type: str,
        correlation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        return self.log_event(
            event_type=event_type,
            level="debug",
            data=data or {},
            correlation_id=correlation_id,
            actor=actor,
            service=service,
        )

    def info(
        self,
        event_type: str,
        correlation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        return self.log_event(
            event_type=event_type,
            level="info",
            data=data or {},
            correlation_id=correlation_id,
            actor=actor,
            service=service,
        )

    def warning(
        self,
        event_type: str,
        correlation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        return self.log_event(
            event_type=event_type,
            level="warning",
            data=data or {},
            correlation_id=correlation_id,
            actor=actor,
            service=service,
        )

    def error(
        self,
        event_type: str,
        correlation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actor: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None,
    ):
        return self.log_event(
            event_type=event_type,
            level="error",
            data=data or {},
            correlation_id=correlation_id,
            actor=actor,
            service=service,
        )


class NoOpEventLogger:
    """No-op event logger that silently ignores all logging calls."""

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return {}, None
        return _noop


_event_logger: Union[EventLogger, NoOpEventLogger, None] = None


def init_event_logger(
    project_id: Optional[str] = None,
    topic_name: Optional[str] = None,
    environment: Optional[str] = None,
    service_name: Optional[str] = None,
    credentials_path: Optional[str] = None,
) -> EventLogger:
    """Initialize the global event logger instance."""
    global _event_logger
    _event_logger = EventLogger(
        project_id=project_id,
        topic_name=topic_name,
        environment=environment,
        service_name=service_name,
        credentials_path=credentials_path,
    )
    logger.info(
        "EventLogger initialized for service=%s, environment=%s",
        _event_logger.service_name,
        _event_logger.environment,
    )
    return _event_logger


def get_event_logger() -> Union[EventLogger, NoOpEventLogger]:
    """Get the global event logger instance, or a NoOp logger if not initialized."""
    global _event_logger
    if _event_logger is None:
        logger.debug("EventLogger not initialized, using NoOpEventLogger")
        return NoOpEventLogger()
    return _event_logger
