# InferenceServer

## Installation
InferenceServer depends on:
- Docker and nvidia-docker2 to be installed.
- A GPU installed with appropriate nvidia and CUDA drivers

### How to host
- Clone repo
- Adjust .env.example and put in .env in root. Make sure you have a vaild domain
- Add certificates in traefik/certs and make sure the naming matches traefik/configuration/config.toml. There is a script to generate certs in traefik/certs/generate_self_signed_certs. Make sure the domain you host on is equal to the certificate.
- run `docker-compose up -d`

### How to use
The public api can be inspected and tested at https://<domain>/docs
Generally the following two methods are useful:

#### Post model
This is a HTTP POST on https://<domain>/api/tasks/
With python requests it can be reached like:
```
with open("path/to/model.zip", "br") as r:
    res = requests.post(url=https://<domain>/api/tasks/,  
                        params = {  
                            "container_tag": mathiser/inference_server_models:some_inference_stuff,  
                            "human_readable_id": "easy_to_write_must_be_unique", 
                            "description": "This model is a test inference model",  
                            "model_available": True,  
                            "use_gpu": True  
                        },  
                        files = {"zip_file": r})  
```
Note, that sending a `model.zip` is optional. If not send, you should set `model_available: False`.
Then you probably want to submit a job. This can be done like:
```
with open("input.zip", "br") as r:
    res = requests.post(url=https://<domain>/api/tasks/,
                        params={"model_human_readable_id": "easy_to_write_must_be_unique"})
    if res.ok:
        task_uid = json.loads(res.content)
```

When a task is submitted, and you have successfully received the task_uid, you poll the server to check if the job is done.
```
res = requests.get(url=https://<domain>/api/tasks/{uid})
if res.ok:
  with open("output.zip", "bw") as f:
    f.write(res.content)
else:
  <check the status codes below>
```

Status codes on task polling:
- 500: Internal server error
- 551: Task pending
- 552: Task failed
- 553: Task finished, but output zip not found.
- 554: Not found


It completely normal to receive 554 immediatly after a task is posted, but you should receive 551 soon after.

### How to reset
- Doing a soft reset keeping all data intact:  
`docker-compose down && docker-compose up -d`

- Doing a slightly harder reset pruning volumes that might have caused a failure:  
```
docker-compose down
docker volume prune  # Watchout if you have not binded the datadir to persistent storage!
docker-compose up -d
```

- Full take down of the entire server and start anew:  
```
docker-compose down
docker volume prune
rm mount  # or where the persistent data store is located
docker-compose up -d
```
Repost your models to the server with your own script or go to `https://inferenece_server.domain.com/docs` and add them manually (remember to set `ALLOW_PUBLIC_POST_MODEL` to something/anything in your `.env` (e.g. `ALLOW_PUBLIC_POST_MODEL=1`) to post models.)  

A commandline client is under development [here](https://github.com/mathiser/inference_server_client)
## Model creation
See this [repo](https://github.com/mathiser/inference_server_models) for examples and documentation
