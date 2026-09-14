# Redis Clone

A Redis-inspired in-memory database built from scratch in Python to understand networking, database internals, persistence, replication, high availability, Sentinel, concurrency, and sharding.

## Features

* TCP-based client-server architecture

* RESP protocol parsing

* Redis-like command execution

* In-memory key-value storage

* Key expiration and TTL

* Pub/Sub

* Transactions

* Primary-replica replication

* Full synchronization using database snapshots

* Live replication of write commands

* Replication IDs and offsets

* Replication backlog concepts

* AOF persistence

* AOF loading and rewriting

* Concurrent client handling using `select`

* Replica server architecture

* Replica concurrency using threads or an event loop

* Redis-compatible client connections to replicas

* Sentinel-style primary health monitoring

* Consecutive failure detection

* Primary recovery detection

* Replica monitoring

* Replica selection

* Replica promotion

* Automatic failover

* Primary discovery

* Client redirection

* Sharding

* Key-based request routing

* Hash-based data partitioning

* Multiple primary shards

* Replication per shard

* Failover per shard

* Cross-shard command handling

* Data migration and rebalancing concepts

## Architecture

```
                         Client
                           |
                           v
                    Redis-compatible
                         Router
                           |
              ┌────────────┼────────────┐
              v            v            v
          Shard 1       Shard 2       Shard 3
          Primary       Primary       Primary
             |             |             |
          Replica        Replica        Replica
```

## Replication

```
                    Primary
                     :6379
                       |
          ┌────────────┴────────────┐
          |                         |
          v                         v
      Replica 1                 Replica 2
       :6380                      :6381
```

The replica connects to the primary, receives an initial database snapshot, restores it locally, and then applies live replication commands received from the primary.

## Sentinel

Sentinel monitors primary and replica nodes, detects primary failures, selects a suitable replica, and supports automatic failover.

```
                       Sentinel
                      /        \
                     v          v
                 Primary      Replica
                  :6379        :6380
                    |
                    | Replication
                    v
                  Replica
```

Sentinel responsibilities include:

* Primary health monitoring

* Replica health monitoring

* Failure detection

* Recovery detection

* Replica selection

* Replica promotion

* Primary discovery

* Client redirection

* Automatic failover

## Sharding

Sharding distributes data across multiple primary nodes instead of storing the entire dataset on one server.

```
Client
  |
  v
Shard Router
  |
  ├── Shard 1 → Primary 1
  ├── Shard 2 → Primary 2
  └── Shard 3 → Primary 3
```

Keys are routed to shards using a hashing strategy:

```
hash(key) % number_of_shards
```

Each shard can have its own replica and failover mechanism.

Sharding covers:

* Static shard configuration

* Key-based routing

* Hash-based partitioning

* Shard routers

* Multiple primary nodes

* Replication per shard

* Failover per shard

* Cross-shard commands

* Data migration

* Rebalancing

* Consistent hashing

* Slot-based partitioning

## Technologies

* Python

* TCP sockets

* RESP protocol

* `select`

* Threads

* Pickle

* JSON

* Append-Only File persistence

## Project Structure

```
.
├── server.py
├── replica.py
├── sentinel.py
├── commands.py
├── parser.py
├── database.py
├── pubsub.py
├── aof_parser.py
├── config.json
└── README.md
```

## Disclaimer

This is an educational Redis-inspired implementation built from scratch. It is not intended to be production-ready or fully compatible with Redis or Valkey.
