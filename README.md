# Wise concepts

Building up my understanding of Fintech essentials in preparation for interview at Wise.

Concepts used:
- Observer pattern with Kafka
- Idempotency keys

## Setup

1. Install dependencies for main application

```bash
uv sync
```

## Running the application

1. Start Kafka container

```bash
docker compose up -d
```

2. Create topics (must be done every restart!):

```bash
docker compose exec -it kafka \
  /opt/kafka/bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic sms_request
```

3. Run the FastAPI app
```bash
cd src
uv run -m uvicorn main:app --port 8080
```

## Tests

### Circuit breaker

1. Start Kafka container

```bash
docker compose up -d
```

2. Set TEST_CIRCUIT_BREAKER environment variable before starting the app, which causes service methods to fail on purpose.

```bash
cd src
TEST_CIRCUIT_BREAKER=1 uv run -m uvicorn main:app --port 8080
```

3. Create topics (must be done every restart!):

```bash
docker compose exec -it kafka \
  /opt/kafka/bin/kafka-topics.sh --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 1 \
  --partitions 3 \
  --topic sms_request
```

4. Run the failure simulation script to flood the services and see what happens!

```bash
./scripts/testing/test_circuit_breaker.sh
```

## Planned additional features

- Add Redis docker container and make use of the idempotency key
- Add Postgres container to do atomic transactions and saga pattern
- Dockerize main application
- Use Kafka AdminClient to create topics programatically

## Known issues

- After the Kafka consumer in SMSService receives at least one message, Ctrl+C may not be able to terminate the program. The loop will continue.
