#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Arg must be a version string - e.g.: 1.2.3"
    exit 1
fi

#!/bin/bash

docker build ./consumer/ -t mathiser/inference_server_consumer:$1
docker build ./controller/ -t mathiser/inference_server_controller:$1


docker push mathiser/inference_server_controller:$1
docker push mathiser/inference_server_consumer:$1
