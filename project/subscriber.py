import json
import pika
import functools
import threading

from .database import handle_accept_visit, handle_delete_visit
import logging
from . import settings
from builtins import input

def ack_message(channel, delivery_tag):
    """Note that `channel` must be the same pika channel instance via which
    the message being ACKed was retrieved (AMQP protocol constraint).
    """
    if channel.is_open:
        channel.basic_ack(delivery_tag)
    else:
        # Channel is already closed, so we can't ACK this message;
        # log and/or do something that makes sense for your app in this case.
        pass

def do_work(connection, channel, method_frame, body):
    thread_id = threading.get_ident()
    fmt1 = 'Thread id: {} Delivery tag: {} Message body: {}'
    logging.info(fmt1.format(thread_id, method_frame.delivery_tag, body))
    # Sleeping to simulate 10 seconds of work
    event_dict = json.loads(body)
    if method_frame.exchange[-14:] == 'visit.accepted':
        handle_accept_visit(event_dict)
    elif method_frame.exchange[-13:] == 'visit.deleted':
        handle_delete_visit(event_dict)

    cb = functools.partial(ack_message, channel, method_frame.delivery_tag)
    connection.add_callback_threadsafe(cb)

def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    t = threading.Thread(target=do_work, args=(connection, channel, method_frame, body))
    t.start()
    threads.append(t)

def start_rabbitmq_listener():
    if settings.RABBIT_USERNAME:
        credentials = pika.credentials.PlainCredentials(
            username=settings.RABBIT_USERNAME,
            password=settings.RABBIT_PASSWORD,
        )
        rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(settings.RABBIT_URL, credentials=credentials))
    else:
        rabbit_connection = pika.BlockingConnection(pika.ConnectionParameters(settings.RABBIT_URL))

    queue_name = '%s.%s' % (settings.RABBIT_ENV, settings.QUEUE_NAME)

    rabbit_channel = rabbit_connection.channel()
    rabbit_channel.queue_declare(queue=queue_name, auto_delete=False, durable=True, arguments={"x-queue-type": "quorum"})
    rabbit_channel.queue_bind(queue=queue_name, exchange='%s.visit.deleted' % settings.RABBIT_ENV)
    rabbit_channel.queue_bind(queue=queue_name, exchange='%s.visit.accepted' % settings.RABBIT_ENV)

    threads = []

    on_message_callback = functools.partial(on_message, args=(rabbit_connection, threads))
    rabbit_channel.basic_consume(queue_name, on_message_callback)

    try:
        rabbit_channel.start_consuming()
    except KeyboardInterrupt:
        rabbit_channel.stop_consuming()

    # Wait for all to complete
    for thread in threads:
        thread.join()

    rabbit_connection.close()
