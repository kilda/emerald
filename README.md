# Zookeeper Emerald Dashboard

## Build

`docker build -t emerald .`

## Run
`kilda_docker_net=$(docker network list | grep open-kilda | awk '{print $1}')`
```
docker \
    run \
    --name emerald \
    -d \
    -e ZK_HOSTS=zookeeper.pendev:2181 \
    -e ZK_ROOT=/kilda \
    -p 1090:1090 \
    --network=$kilda_docker_net  \
    emerald
```

## Swagger

`http://localhost:8080/docs`

## Board

`http://localhost:8080`