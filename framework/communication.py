#
# communication.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    topic: str  # name of the topic, e.g. `database_updated`, `websocket/<plugin_name>`
    payload: Any = None  # content of the message. Can be anything and can be `None`
    sender: Any = None  # either name (str) or the obj. But I think name is better.
    receiver: Any = None  # sure? Broadcasting doesn't have only one message.


class Topics:
    _clients = set()

    # TODO: Either deliver every message to every plugin or maintain a list with "interested plugins"
    """
    Implements a messaging system where messages are exchanged over topics. Clients can subscribe to
    any topic and will get notified via a callback once a message appears on that topic.
    Every client can publish messages on all topics.

    Message structure:
    {
        "topic": "topic_name",
        "sender": "sender_name",
        "payload": "contents_of_the_message"
    }
    """
    def __init__(self):
        raise RuntimeWarning("Topics class is not supposed to be instantiated")

    # TODO: Add a way to define message structure beforehand and enforce it.
    # def define_message_type(self, message_structure):
    #     """
    #     message_structure would contain a python object with type names in it. The messaging entity can
    #     can then check any incoming message to comply with this scheme before sending it to the subscribers.
    #
    #     {
    #         "property1": Int,
    #         "property2": str
    #     }
    #     """
    #     pass

    @classmethod
    def register(cls, client):
        """
        Registers a client (caller) for a topic.
        The callback will be called every time the a new message is sent on that topic.
        callbacks are ought to return quickly.
        """
        cls._clients.add(client)

    @classmethod
    def unregister(cls, client):
        """ Removes the given callback from the topic. """
        try:
            cls._clients.remove(client)
        except ValueError:
            pass

    @classmethod
    def send_message(cls, message):
        """ Will distribute the message to all subscribers by calling their callback. """
        if not isinstance(message, Message):
            print("!!! Message has wrong type:", type(message))
        for client in cls._clients:
            client.receive_message(message)

