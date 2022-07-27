import pika, sys, os, time, threading

results_counter = 0

def results_handler():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))

    results_channel = connection.channel()

    results_channel.queue_declare(queue="results")

    def callback(ch, method, properties, body):
        global results_counter
        print(f"Received result \"{body}\"")
        results_counter += 1
        ch.basic_ack(delivery_tag=method.delivery_tag)

    results_channel.basic_consume(
        queue="results", on_message_callback=callback, auto_ack=False
    )

    results_channel.start_consuming()    


def main():
    global results_counter

    result_thread = threading.Thread(target = results_handler)
    result_thread.start()

    connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
    tasks_channel = connection.channel()

    tasks_channel.queue_declare(queue="tasks")

    task_counter = 0

    with open("server.py", "rt") as input_file:
        for s in input_file:
            if s:
                task_counter += 1
                tasks_channel.basic_publish(exchange="", routing_key="tasks", body=s)
            
    time.sleep(10)

    print(f"{results_counter} results of {task_counter} received")

    connection.close()


if __name__ == "__main__":
    main()