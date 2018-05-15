#!/bin/sh

export PYTHONPATH=/wallaroo-src/machida:$PYTHONPATH

cd `dirname "$0"`

machida --application-module star_leaders \
  --kafka_source_topic gharchive --kafka_source_brokers kafka:9092 \
  --kafka_sink_topic leaderboard --kafka_sink_brokers kafka:9092 \
  --kafka_sink_max_message_size 250000 --kafka_sink_max_produce_buffer_ms 10 \
  --metrics wallaroo_metrics_ui:5001 \
  --ponynoblock --ponythreads=1 \
  --join wallaroo_primary_worker:12500 \
  --name secondary_worker_1
