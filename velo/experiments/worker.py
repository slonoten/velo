import pika, sys, os


def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    tasks_channel = connection.channel()

    tasks_channel.queue_declare(queue="tasks")

    results_channel = connection.channel()

    results_channel.queue_declare(queue="results")

    def callback(ch, method, properties, body):
        print(f"Received {body}")
        results_channel.basic_publish(
            exchange="", routing_key="results", body=f'Processed "{body}"'
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    tasks_channel.basic_consume(
        queue="tasks", on_message_callback=callback, auto_ack=False
    )

    print(" [*] Waiting for messages. To exit press CTRL+C")
    tasks_channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
