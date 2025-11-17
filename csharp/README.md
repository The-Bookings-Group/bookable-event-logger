# Bookable.EventLogger (.NET)

Internal .NET SDK for publishing Bookable events to Pub/Sub, following the
shared Event Logging Contract.

## Usage

```csharp
using Bookable.EventLogger;

var logger = new EventLogger();
await logger.InfoAsync(
    eventType: "email.sync.batch.started",
    data: new Dictionary<string, object>
    {
        ["accounts_total"] = 12,
        ["sync_type"] = "cron"
    },
    correlationId: "req-123",
    actor: new Dictionary<string, object>
    {
        ["kind"] = "internal_service",
        ["source"] = "scheduler"
    }
);

await logger.LogAsync(
    level: "warning",
    eventType: "email.sync.batch.slow",
    data: new Dictionary<string, object>
    {
        ["duration_ms"] = 120000
    },
    correlationId: "req-123"
);
```

## Environment variables

- `LOG_GCP_PROJECT`
- `LOG_TOPIC` (default: `events`)
- `LOG_ENVIRONMENT`
- `LOG_SERVICE_NAME`
- `LOG_GCP_CREDENTIALS` (path to service account JSON for local/dev)
