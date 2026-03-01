import traceback
import asyncio
import json
from typing import Optional
import logging
from confluent_kafka.aio import AIOConsumer
from confluent_kafka import Message
from fastapi import FastAPI
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class SMSService(BaseService):
    # For singleton
    instance: Optional["SMSService"] = None

    consumer: AIOConsumer
    topic: str
    running: bool

    # Used for teardown
    consumer_task: Optional[asyncio.Task] = None

    def __init__(self):
        self.consumer = AIOConsumer(
            {
                "bootstrap.servers": "localhost:9092",
                "enable.auto.commit": "false",  # Manual commit for precise control
                "group.id": "sms-group",
                "auto.offset.reset": "earliest",
                "partition.assignment.strategy": "cooperative-sticky",
            }
        )
        self.topic = "sms_request"
        self.running = False

    @classmethod
    async def get_instance(cls):
        if not cls.instance:
            cls.instance = await cls.create()
        return cls.instance

    @classmethod
    async def create(cls):
        # AsyncIO Pattern: Non-blocking consumer with manual offset management
        # Callbacks will be scheduled on the event loop automatically

        # Create SMSService
        service = SMSService()

        # Run the consumer
        service.consumer_task = asyncio.create_task(service.run_consumer())

        # Return the service
        return service

    async def run_consumer(self):
        # AsyncIO Pattern: Async rebalance callbacks
        # These callbacks can perform async operations safely within the event loop
        async def on_assign(consumer, partitions):
            # Calling incremental_assign is necessary to pause the assigned partitions
            # otherwise it'll be done by the consumer after callback termination.
            await consumer.incremental_assign(partitions)
            await consumer.pause(partitions)  # Demonstrates async partition control
            logger.debug(f"on_assign {partitions}")
            # Resume the partitions as it's just a pause example
            await consumer.resume(partitions)

        async def on_revoke(consumer, partitions):
            logger.debug(
                f"before on_revoke {partitions}",
            )
            try:
                # AsyncIO Pattern: Non-blocking commit during rebalance
                await consumer.commit()  # Ensure offsets are committed before losing partitions
            except Exception as e:
                logger.info(f"Error during commit: {e}")
            logger.debug(f"after on_revoke {partitions}")

        async def on_lost(consumer, partitions):
            logger.debug(f"on_lost {partitions}")

        try:
            await self.consumer.subscribe(
                [self.topic],
                on_assign=on_assign,
                on_revoke=on_revoke,
                # Remember to set a on_lost callback
                # if you're committing on revocation
                # as lost partitions cannot be committed
                on_lost=on_lost,
            )
            i = 0
            self.running = True
            while self.running:
                try:
                    # AsyncIO Pattern: Non-blocking message polling
                    # poll() returns a coroutine that yields control back to the event loop
                    message = await self.consumer.poll(1.0)
                    if message is None:
                        logger.info("No message.")
                        continue
                    else:
                        logger.info("Message received!")

                    assert isinstance(message, Message)

                    err = message.error()
                    if err:
                        logger.error(f"Error: {err}")
                    else:
                        message_value = message.value()
                        if message_value:
                            # Parse message to python dict
                            sms_data = json.loads(message_value.decode("utf-8"))

                            # Send SMS
                            user_id = sms_data["from"]
                            sms_contents = f"You have received {sms_data['amount']}{sms_data['currency']} from User {user_id}."
                            self.send_sms(user_id, sms_contents)

                        # Tell Kafka that we are done with this message
                        await self.consumer.commit(message=message, asynchronous=True)
                        logger.info("Offset committed after successful SMS send")

                        i += 1
                except asyncio.CancelledError:
                    self.running = False
                except Exception:
                    traceback.print_exc()
        finally:
            # Let FastAPI take care of unsubscribe
            self.running = False

    def send_sms(self, recipient_user_id: str, message: str):
        # Simulated SMS
        success_message = f"SMS sent to User {recipient_user_id}: {message}"
        logger.info(success_message)

    async def cleanup(self):
        if self.consumer_task:
            await self.consumer.unsubscribe()  # Leave consumer group gracefully
            await self.consumer.close()  # Close connections and stop background tasks
            self.consumer_task.cancel()

            try:
                await self.consumer_task
            except asyncio.CancelledError:
                logger.debug("SMSService consumer gracefully shut down.")

    def register_fastapi_routes(self, app: FastAPI):
        pass
