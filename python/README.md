
# bookable-event-logger (Python)

Internal Python SDK for publishing Bookable events to Pub/Sub, following the
shared Event Logging Contract.

## Installation

From this repo root:

```bash
cd python
pip install -e .
```

## Usage

```python
from bookable_event_logger import init_event_logger, get_event_logger

# during startup
init_event_logger()  # uses env vars

# later in code
logger = get_event_logger()

logger.info(
    event_type="email.sync.batch.started",
    correlation_id="req-123",
    data={"accounts_total": 12, "sync_type": "cron"},
    actor={"kind": "internal_service", "source": "scheduler"},
)
```

## Environment variables

- `LOG_GCP_PROJECT`
- `LOG_TOPIC` (default: `events`)
- `LOG_ENVIRONMENT`
- `LOG_SERVICE_NAME`
- `LOG_GCP_CREDENTIALS` (path to service account JSON for local/dev)
