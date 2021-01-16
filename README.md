# Zookeeper Emerald Dashboard

## Build

`docker build -t emerald .`

## Run

`docker run -d -p 8080:8080 --network="zk_net_id"  emerald`