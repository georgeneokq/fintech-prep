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
uv run uvicorn main:app --port 8080
```

## Planned additional features

- Add Redis docker container and make use of the idempotency key
- Add Postgres container to do atomic transactions and saga pattern
- Dockerize main application

## Known issues

- After the Kafka consumer in SMSService receives at least one message, Ctrl+C may not be able to terminate the program. The loop will continue.
