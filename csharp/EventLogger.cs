using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Google.Api.Gax.Grpc;
using Google.Apis.Auth.OAuth2;
using Google.Cloud.PubSub.V1;
using Grpc.Auth;
using Grpc.Core;

namespace Bookable.EventLogger
{
    public class EventLogger
    {
        private readonly string _projectId;
        private readonly string _topicName;
        private readonly string _environment;
        private readonly string _serviceName;
        private readonly string _credentialsPath;
        private readonly PublisherClient _publisher;
        private readonly TopicName _topic;

        public EventLogger(
            string? projectId = null,
            string? topicName = null,
            string? environment = null,
            string? serviceName = null,
            string? credentialsPath = null)
        {
            _projectId = projectId ?? Environment.GetEnvironmentVariable("LOG_GCP_PROJECT")
                ?? throw new ArgumentException("LOG_GCP_PROJECT / projectId is required");

            _topicName = topicName ?? Environment.GetEnvironmentVariable("LOG_TOPIC") ?? "events";
            _environment = environment ?? Environment.GetEnvironmentVariable("LOG_ENVIRONMENT")
                ?? throw new ArgumentException("LOG_ENVIRONMENT / environment is required");

            _serviceName = serviceName ?? Environment.GetEnvironmentVariable("LOG_SERVICE_NAME")
                ?? throw new ArgumentException("LOG_SERVICE_NAME / serviceName is required");

            _credentialsPath = credentialsPath ?? Environment.GetEnvironmentVariable("LOG_GCP_CREDENTIALS")
                ?? throw new ArgumentException("LOG_GCP_CREDENTIALS / credentialsPath is required");

            var credential = GoogleCredential.FromFile(_credentialsPath)
                .CreateScoped("https://www.googleapis.com/auth/pubsub");

            ChannelCredentials channelCredentials = credential.ToChannelCredentials();
            var channel = new Channel(
                PublisherServiceApiClient.DefaultEndpoint.Host,
                PublisherServiceApiClient.DefaultEndpoint.Port,
                channelCredentials
            );

            var publisherClient = PublisherServiceApiClient.Create(channel);
            _topic = new TopicName(_projectId, _topicName);
            _publisher = PublisherClient.Create(_topic, client: publisherClient);
        }

        private Dictionary<string, object> BuildEvent(
            string eventType,
            string level,
            IDictionary<string, object>? data,
            string? service,
            string? correlationId,
            IDictionary<string, object>? actor)
        {
            var actorObj = actor ?? new Dictionary<string, object>();
            var dataObj = data ?? new Dictionary<string, object>();
            var serviceName = service ?? _serviceName;

            var evt = new Dictionary<string, object>
            {
                ["event_id"] = Guid.NewGuid().ToString(),
                ["correlation_id"] = correlationId ?? Guid.NewGuid().ToString(),
                ["service"] = serviceName,
                ["event_type"] = eventType,
                ["level"] = level,
                ["environment"] = _environment,
                ["created_at"] = DateTime.UtcNow.ToString("O"),
                ["actor"] = JsonSerializer.Serialize(actorObj),
                ["data"] = JsonSerializer.Serialize(dataObj)
            };

            return evt;
        }

        public async Task<(Dictionary<string, object> Event, string? MessageId)> LogEventAsync(
            string eventType,
            string level,
            IDictionary<string, object>? data = null,
            string? service = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null)
        {
            var evt = BuildEvent(eventType, level, data, service, correlationId, actor);
            var json = JsonSerializer.Serialize(evt);
            var message = new PubsubMessage
            {
                Data = Google.Protobuf.ByteString.CopyFromUtf8(json)
            };

            try
            {
                var messageId = await _publisher.PublishAsync(message);
                return (evt, messageId);
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Failed to publish event to Pub/Sub: {ex}");
                return (evt, null);
            }
        }

        public Task<(Dictionary<string, object> Event, string? MessageId)> LogAsync(
            string level,
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
        {
            return LogEventAsync(eventType, level, data, service, correlationId, actor);
        }

        public Task<(Dictionary<string, object> Event, string? MessageId)> DebugAsync(
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
        {
            return LogEventAsync(eventType, "debug", data, service, correlationId, actor);
        }

        public Task<(Dictionary<string, object> Event, string? MessageId)> InfoAsync(
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
        {
            return LogEventAsync(eventType, "info", data, service, correlationId, actor);
        }

        public Task<(Dictionary<string, object> Event, string? MessageId)> WarningAsync(
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
        {
            return LogEventAsync(eventType, "warning", data, service, correlationId, actor);
        }

        public Task<(Dictionary<string, object> Event, string? MessageId)> ErrorAsync(
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
        {
            return LogEventAsync(eventType, "error", data, service, correlationId, actor);
        }
    }

    public class NoOpEventLogger
    {
        public Task LogEventAsync(
            string eventType,
            string level,
            IDictionary<string, object>? data = null,
            string? service = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null)
            => Task.CompletedTask;

        public Task LogAsync(
            string level,
            string eventType,
            IDictionary<string, object>? data = null,
            string? correlationId = null,
            IDictionary<string, object>? actor = null,
            string? service = null)
            => Task.CompletedTask;

        public Task DebugAsync(string eventType, IDictionary<string, object>? data = null,
            string? correlationId = null, IDictionary<string, object>? actor = null, string? service = null)
            => Task.CompletedTask;

        public Task InfoAsync(string eventType, IDictionary<string, object>? data = null,
            string? correlationId = null, IDictionary<string, object>? actor = null, string? service = null)
            => Task.CompletedTask;

        public Task WarningAsync(string eventType, IDictionary<string, object>? data = null,
            string? correlationId = null, IDictionary<string, object>? actor = null, string? service = null)
            => Task.CompletedTask;

        public Task ErrorAsync(string eventType, IDictionary<string, object>? data = null,
            string? correlationId = null, IDictionary<string, object>? actor = null, string? service = null)
            => Task.CompletedTask;
    }
}
