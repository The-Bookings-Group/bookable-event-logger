
# 📘 Bookable Event Logging Contract

This document defines the **standard event format** used across all Bookable services.
Events are published to **Google Pub/Sub**, then automatically streamed into **BigQuery**
using a BigQuery subscription.

All services **must** follow this structure when publishing events.

---

## 1. Purpose

This contract guarantees:

- Consistent structure across all services  
- Easy cross-service correlation using `correlation_id`  
- Predictable ingestion into BigQuery  
- Backward-compatible evolution of the schema  
- Language-agnostic logging (Python, Node, .NET, etc.)

---

## 2. Event Envelope (Required Fields)

Every event must conform to this schema:

```json
{
  "event_id": "string",
  "correlation_id": "string",
  "service": "string",
  "event_type": "string",
  "level": "string",
  "environment": "string",
  "created_at": "string",
  "actor": "string",
  "data": "string"
}
```

> **Important:** `actor` and `data` **must be JSON strings**, not raw objects.

---

## 3. Field Definitions

### `event_id`

- **Type:** UUID string  
- **Purpose:** Uniquely identifies each event row (primary key).  

### `correlation_id`

- **Type:** UUID string  
- **Purpose:** Groups multiple events belonging to a single logical flow.

### `service`

- **Type:** string  
- **Purpose:** Name of the emitting service (e.g. `email-integration`, `product-match`).

### `event_type`

- **Type:** string  
- **Format:** `<domain>.<feature>.<entity>.<action>`  
- **Examples:** `email.sync.batch.started`, `email.sync.account.completed`.

### `level`

- **Allowed values:** `debug`, `info`, `warning`, `error`.

### `environment`

- **Allowed values:** `dev`, `staging`, `production`.

### `created_at`

- **Format:** ISO-8601 UTC timestamp, e.g. `2025-11-17T13:30:00Z`.

### `actor`

- **Type:** JSON string  
- **Purpose:** Flexible actor metadata (user/service/venue info).

### `data`

- **Type:** JSON string  
- **Purpose:** Event-specific payload (booking, email sync info, etc.).

---

## 4. Environment Variables

All SDKs use the same environment variables:

| Variable            | Purpose                                             |
|---------------------|-----------------------------------------------------|
| `LOG_GCP_PROJECT`   | GCP project ID (`bookings-api-staging`, `...-prod`) |
| `LOG_TOPIC`         | Pub/Sub topic name (usually `events`)              |
| `LOG_ENVIRONMENT`   | Environment (`staging`, `production`, `dev`)       |
| `LOG_SERVICE_NAME`  | Name of the emitting service                       |
| `LOG_GCP_CREDENTIALS` | Path to service account JSON (local dev only)    |

In production, services should use attached service accounts / workload
identity instead of JSON key files.

---

## 5. Pub/Sub → BigQuery

- Pub/Sub topic: `events` (no schema attached).  
- BigQuery dataset: `logging`.  
- BigQuery table: `events`.

Recommended schema:

| Field         | Type      | Mode     |
|---------------|-----------|----------|
| event_id      | STRING    | REQUIRED |
| correlation_id| STRING    | NULLABLE |
| service       | STRING    | REQUIRED |
| event_type    | STRING    | REQUIRED |
| level         | STRING    | REQUIRED |
| environment   | STRING    | REQUIRED |
| created_at    | TIMESTAMP | REQUIRED |
| actor         | STRING    | NULLABLE |
| data          | STRING    | NULLABLE |

BigQuery subscription configuration:

- Subscription type: **BigQuery subscription**  
- Schema configuration: **Use table schema**  
- Dead-letter topic: recommended, with ~5 attempts.

---

## 6. Example Event

```json
{
  "event_id": "cae4a24e-75d0-444e-b609-d3f78e26158c",
  "correlation_id": "9c64b44b-1933-4ea3-b537-24bf0cde8cbe",
  "service": "email-integration",
  "event_type": "email.sync.account.completed",
  "level": "info",
  "environment": "staging",
  "created_at": "2025-11-17T11:58:21Z",
  "actor": "{"kind":"internal_service","source":"scheduler"}",
  "data": "{"account_id":"af4c2151-dca3-4383-a42a-22a9b8820ef8","sync_type":"cron","emails_processed":2}"
}
```

---

## 7. Backward Compatibility

- Adding new fields: **allowed**  
- Removing or renaming fields: **not allowed**  
- Changing field types: **not allowed** (except JSON → STRING for `actor`/`data`)  
- Adding properties inside `actor` / `data`: **always allowed**
