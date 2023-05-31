import os

import dotenv

from consumer.consumer_rabbitmq_impl import ConsumerRabbitImpl
from database.database_rest_impl import DBRestImpl
from database_client.db_client_requests_impl import DBClientRequestsImpl

#dotenv.load_dotenv()


def main():
    db_client = DBClientRequestsImpl(base_url=os.environ.get("API_URL"))
    db = DBRestImpl(db_client=db_client)
    consumer = ConsumerRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"),
                                  port=int(os.environ.get("RABBIT_PORT")),
                                  db=db,
                                  unfinished_queue_name=os.environ.get("UNFINISHED_JOB_QUEUE"),
                                  finished_queue_name=os.environ.get("FINISHED_JOB_QUEUE"),
                                  prefetch_value=int(os.environ.get("PREFETCH_VALUE")),
                                  api_url=os.environ.get("API_URL"),
                                  api_output_zips=os.environ.get("API_OUTPUT_ZIPS"),
                                  volume_sender_docker_tag=os.environ.get("VOLUME_SENDER_DOCKER_TAG"),
                                  network_name=os.environ.get("NETWORK_NAME"),
                                  gpu_uuid=os.environ.get("GPU_UUID"),
                                  )

    consumer.consume_unfinished()


if __name__ == "__main__":
    main()
