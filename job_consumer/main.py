import os

import dotenv

from consumer.consumer_rabbitmq_impl import ConsumerRabbitImpl
from job.job_docker_impl import JobDockerImpl
from database.database_rest_impl import DBRestImpl

dotenv.load_dotenv()
def main():
    db = DBRestImpl(api_url=os.environ.get("API_URL"))
    consumer = ConsumerRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"),
                        port=int(os.environ.get("RABBIT_PORT")),
                        db=db,
                        JobClass=JobDockerImpl)

    consumer.consume_unfinished()

if __name__ == "__main__":
    main()