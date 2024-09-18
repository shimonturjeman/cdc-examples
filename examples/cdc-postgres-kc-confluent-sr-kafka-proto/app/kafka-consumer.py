import argparse
import uuid
from dataclasses import dataclass

import device_pb2
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry.protobuf import ProtobufDeserializer


def _instantiate_unique_consumer_group():
    return f"device-consumer-group-{uuid.uuid4()}"


@dataclass
class Device:
    id: int
    name: str
    dev_type: str

    def __str__(self):
        return f"Device: <ID: {self.id}, Name: {self.name}, Type: {self.dev_type}>"


def _get_consumer_config(args):
    return {
        'bootstrap.servers': args.bootstrap_servers,
        'group.id': args.group,
        'auto.offset.reset': args.offset_reset
    }

def main(args):
    protobuf_deserializer = ProtobufDeserializer(device_pb2.Device,
                                                 {'use.deprecated.format': False})
    topic = args.topic
    consumer = Consumer(_get_consumer_config(args))

    consumer.subscribe([topic])

    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            deserialized_msg = protobuf_deserializer(msg.value(), SerializationContext(topic, MessageField.VALUE))
            device = Device(id=deserialized_msg.id,
                            name=deserialized_msg.name,
                            dev_type=deserialized_msg.dev_type)

            if device is not None:
                print(device)

        except KeyboardInterrupt:
            break

    consumer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="ProtobufDeserializer example")
    parser.add_argument('-b', dest="bootstrap_servers", required=True, help="Bootstrap broker(s) (host[:port])")
    parser.add_argument('-s', dest="schema_registry", required=True, help="Schema Registry (http(s)://host[:port]")
    parser.add_argument('-t', dest="topic", required=True, help="Topic name")
    parser.add_argument('-o', dest="offset_reset", default="earliest", help="Offset reset")
    parser.add_argument('-g', dest="group", default=_instantiate_unique_consumer_group(), help="Consumer group")

    main(parser.parse_args())