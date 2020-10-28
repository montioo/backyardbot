#
# communication.py
# backyardbot
#
# Created: October 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from collections import defaultdict


class Topics:
    _topics = defaultdict(lambda: [])

    # TODO: Make the whole thing work with asyncio
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
    def register(cls, topic, callback):
        """
        Registers a client (caller) for a topic.
        The callback will be called every time the a new message is sent on that topic.
        callbacks are ought to return quickly.
        """
        cls._topics[topic].append(callback)

    @classmethod
    def unregister(cls, topic, callback):
        """ Removes the given callback from the topic. """
        try:
            cls._topics[topic].remove(callback)
        except ValueError:
            pass

    @classmethod
    def send_message(cls, topic, message):
        """ Will distribute the message to all subscribers by calling their callback. """
        # TODO: Is the sender in the message necessary?
        for callback in cls._topics[topic]:
            callback(message)

