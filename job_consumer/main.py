import os

import dotenv

from database.database import DB
from consumer.consumer_rabbitmq_impl import ConsumerRabbitImpl
from job.job_docker_impl import JobDockerImpl

dotenv.load_dotenv()
def main():
    db = DB(api_url=os.environ.get("API_URL"))
    consumer = ConsumerRabbitImpl(host=os.environ.get("RABBIT_HOSTNAME"),
                        port=int(os.environ.get("RABBIT_PORT")),
                        db=db,
                        JobClass=JobDockerImpl)

    consumer.consume_unfinished()

if __name__ == "__main__":
    main()