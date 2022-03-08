docker run -it --rm --network=inference_server_default -e PYTHONUNBUFFERED=1 -v /var/run/docker.sock:/var/run/docker.sock -v $(realpath models):/models post_models

