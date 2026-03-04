#!/bin/bash
set -e

KAFKA_BOOTSTRAP="localhost:29092"

for topic in re.listings re.contacts re.market re.notifications re.showings re.transactions re.agent.requests re.agent.results; do
    echo "Creating topic: $topic"
    kafka-topics --create \
        --bootstrap-server "$KAFKA_BOOTSTRAP" \
        --replication-factor 1 \
        --partitions 3 \
        --topic "$topic" \
        --if-not-exists
done

echo "All topics created successfully."
