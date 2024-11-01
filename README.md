## Build the Docker image 
```md
docker build -t discord_bot .
```

## Run theDocker container
```md
docker run -d --name discord_bot -v /var/run/docker.sock:/var/run/docker.sock discord_bot
```
