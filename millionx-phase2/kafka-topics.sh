#!/bin/bash

KAFKA_CONTAINER="millionx-kafka"

echo "Creating Kafka topics for MillionX Phase 2..."

# Source topics (Raw ingestion)
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic source.social.tiktok \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic source.social.facebook \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic source.market.shopify \
  --partitions 4 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic source.market.daraz \
  --partitions 4 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic context.weather \
  --partitions 2 \
  --replication-factor 1 \
  --config retention.ms=2592000000 \
  --bootstrap-server localhost:9092

# Sink topics (Processed data)
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic sink.snowflake.orders \
  --partitions 4 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic sink.weaviate.vectors \
  --partitions 6 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic enriched.weaviate.vectors \
  --partitions 6 \
  --replication-factor 1 \
  --bootstrap-server localhost:9092

# Dead Letter Queues
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic dead-letters-social \
  --partitions 2 \
  --replication-factor 1 \
  --config retention.ms=1209600000 \
  --bootstrap-server localhost:9092

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic dead-letters-market \
  --partitions 2 \
  --replication-factor 1 \
  --config retention.ms=1209600000 \
  --bootstrap-server localhost:9092

echo "✅ All topics created successfully!"
echo ""
echo "To list all topics, run:"
echo "docker exec millionx-kafka kafka-topics --list --bootstrap-server localhost:9092"
