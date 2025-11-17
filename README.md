# Bookable Event Logger

Cross-language event logging SDKs for Bookable services:

- Python
- Node.js
- C# (.NET)

All SDKs implement the same **Event Logging Contract**, and publish structured
events to **Google Pub/Sub**, which are then streamed into **BigQuery** via a
BigQuery subscription.

See [`CONTRACT.md`](./CONTRACT.md) for the full event schema and expectations.

## Language SDKs

- [`python/`](./python) – Python package
- [`node/`](./node) – Node.js package
- [`csharp/`](./csharp) – .NET package

Each SDK:

- Reads config from the same environment variables
- Produces identical event envelopes
- Handles `actor` and `data` as JSON-encoded strings
- Exposes convenience methods: `debug`, `info`, `warning`, `error`, and generic `log`
