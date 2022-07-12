#!/bash/bin
source .env
docker run \
  -dit \
  --env-file .env \
  --network inference_server_private \
  -e GPU_UUID=$1 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  mathiser/inference_server:job_consumer_dev