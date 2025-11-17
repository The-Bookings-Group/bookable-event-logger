const { PubSub } = require("@google-cloud/pubsub");
const { v4: uuidv4 } = require("uuid");

class EventLogger {
  constructor(options = {}) {
    this.projectId = options.projectId || process.env.LOG_GCP_PROJECT;
    this.topicName = options.topicName || process.env.LOG_TOPIC || "events";
    this.environment = options.environment || process.env.LOG_ENVIRONMENT;
    this.serviceName = options.serviceName || process.env.LOG_SERVICE_NAME;
    this.credentialsPath =
      options.credentialsPath || process.env.LOG_GCP_CREDENTIALS;

    const missing = [];
    if (!this.projectId) missing.push("LOG_GCP_PROJECT / projectId");
    if (!this.topicName) missing.push("LOG_TOPIC / topicName");
    if (!this.environment) missing.push("LOG_ENVIRONMENT / environment");
    if (!this.serviceName) missing.push("LOG_SERVICE_NAME / serviceName");
    if (!this.credentialsPath)
      missing.push("LOG_GCP_CREDENTIALS / credentialsPath");

    if (missing.length > 0) {
      throw new Error(
        "Missing required config for EventLogger: " + missing.join(", ")
      );
    }

    this.pubsub = new PubSub({
      projectId: this.projectId,
      keyFilename: this.credentialsPath,
    });

    this.topic = this.pubsub.topic(this.topicName);
  }

  _buildEvent({ eventType, level, data, service, correlationId, actor }) {
    const serviceName = service || this.serviceName;
    const actorObj = actor || {};
    const dataObj = data || {};

    return {
      event_id: uuidv4(),
      correlation_id: correlationId || uuidv4(),
      service: serviceName,
      event_type: eventType,
      level,
      environment: this.environment,
      created_at: new Date().toISOString(),
      actor: JSON.stringify(actorObj),
      data: JSON.stringify(dataObj),
    };
  }

  async logEvent({ eventType, level, data, service, correlationId, actor }) {
    const event = this._buildEvent({
      eventType,
      level,
      data,
      service,
      correlationId,
      actor,
    });

    const payload = Buffer.from(JSON.stringify(event));

    try {
      const [messageId] = await this.topic.publishMessage({ data: payload });
      return { event, messageId };
    } catch (err) {
      console.error("Failed to publish event to Pub/Sub:", err);
      return { event, messageId: null };
    }
  }

  log(level, { eventType, correlationId, data, actor, service } = {}) {
    return this.logEvent({
      eventType,
      level,
      data: data || {},
      correlationId,
      actor,
      service,
    });
  }

  debug(params) {
    return this.logEvent({ ...params, level: "debug" });
  }

  info(params) {
    return this.logEvent({ ...params, level: "info" });
  }

  warning(params) {
    return this.logEvent({ ...params, level: "warning" });
  }

  error(params) {
    return this.logEvent({ ...params, level: "error" });
  }
}

class NoOpEventLogger {
  async logEvent() {}
  async log() {}
  async debug() {}
  async info() {}
  async warning() {}
  async error() {}
}

let _eventLogger = null;

function initEventLogger(options = {}) {
  _eventLogger = new EventLogger(options);
  return _eventLogger;
}

function getEventLogger() {
  if (!_eventLogger) {
    return new NoOpEventLogger();
  }
  return _eventLogger;
}

module.exports = {
  EventLogger,
  NoOpEventLogger,
  initEventLogger,
  getEventLogger,
};
