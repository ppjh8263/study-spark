import sys
from typing import Union, Callable, Any, Optional, Sequence, Dict
from confluent_kafka.cimpl import Producer

from producers.base_producer import BaseProducer
from providers.base_provider import BaseProvider
from functools import partial


def default_delivery_callback(err, msg):
    if err:
        sys.stderr.write("%% Message failed delivery: %s\n" % err)
    else:
        sys.stderr.write(
            "%% Message delivered to %s [%d] @ %d\n"
            % (msg.topic(), msg.partition(), msg.offset())
        )


class SimpleProducer(BaseProducer):
    def __init__(
        self,
        topic,
        broker_list,
        producer_function: Union[str, Callable[..., Any]] = None,
        producer_function_args: Optional[Sequence[Any]] = None,
        producer_function_kwargs: Optional[Dict[Any, Any]] = None,
        token_provider: BaseProvider = None,
        secure_protocol: str = "SASL_SSL",
        sasl_mechanism: str = "OAUTHBEARER",
        delivery_callback: Callable[..., Any] = default_delivery_callback,
        poll_timeout: float = 0,
        partitioner: Optional[Callable[[str], int]] = None,
        synchronous: bool = False,
        kafka_config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.producer_function = producer_function or ""
        self.producer_function_args = producer_function_args or ()
        self.producer_function_kwargs = producer_function_kwargs or {}
        self.topic = topic
        self.token_provider = token_provider

        self.conf = {
            "bootstrap.servers": broker_list,
            "security.protocol": secure_protocol,
            "sasl.mechanisms": sasl_mechanism,
            "debug": "broker,security,protocol,metadata",
        }
        if token_provider:
            self.conf["oauth_cb"] = self.token_provider.get_token
        if kafka_config:
            self.conf.update(kafka_config)
        print("Kafka configuration:", self.conf)
        self.producer = Producer(self.conf)
        self._check_kafka_connection()

        self.delivery_callback = delivery_callback
        self.poll_timeout = poll_timeout
        self.partitioner = partitioner
        self.synchronous = synchronous

        if not (self.topic and self.producer_function):
            raise Exception(
                "topic and producer_function must be provided. Got topic="
                + f"{self.topic} and producer_function={self.producer_function}"
            )

    def produce(self):
        producer_callable = self._get_producer_function()
        message_cnt = 0
        for k, v in producer_callable():
            if message_cnt == 0:
                print("Producing messages...")
            self._produce(k, v)
            message_cnt += 1
        self.producer.flush()

    def _get_producer_function(self):
        producer_callable = self.producer_function
        producer_callable = partial(
            producer_callable,
            *self.producer_function_args,
            **self.producer_function_kwargs,
        )
        return producer_callable

    def _produce(self, _key: str, _value: str):
        produce_args = {
            "topic": self.topic,
            "key": _key,
            "value": _value,
            "on_delivery": self.delivery_callback,
        }
        if self.partitioner is not None:
            produce_args["partition"] = self.partitioner(_key)
        self.producer.produce(**produce_args)
        self.producer.poll(self.poll_timeout)

        if self.synchronous:
            self.producer.flush()

    def _check_kafka_connection(self):
        print("Checking Kafka connection...")
        try:
            self.producer.list_topics(timeout=10)
            return True
        except Exception as e:
            raise TimeoutError(f"Kafka connection check failed: {e}")
