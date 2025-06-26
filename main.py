from producers.simple_producer import SimpleProducer

if __name__ == "__main__":
    topic_name = "local-test-topic"
    broker_list = "localhost:9092"
    producer = SimpleProducer(
        topic=topic_name,
        broker_list=broker_list,
        producer_function=lambda: [(f"key{n}", f"value{n}") for n in range(6000)],
        token_provider=None,
        synchronous=False,
        secure_protocol="PLAINTEXT",
    )
    producer.produce()
