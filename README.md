# Zookeeper Emerald Dashboard

## Build

`docker build -t emerald .`

## Run

`docker run -d -e ZK_HOSTS=zookeeper.pendev:2181 -p 8080:8080 --network="zk_net_id"  emerald`