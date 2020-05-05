import random
import logging

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

try:
    from vk_bot.settings import TOKEN, GROUP_ID
except ImportError:
    exit('Copy settings.py.default and set the token')

log = logging.getLogger('bot')


def configure_log():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    stream_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('bot.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    file_handler.setLevel(logging.DEBUG)

    log.addHandler(stream_handler)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Used Python 3.7
    """
    def __init__(self, group_id, token):
        """

        :param group_id: group id from vk
        :param token: secret token for api access
        """
        self.group_id = group_id
        self.token = token

        self.vk = vk_api.VkApi(token=token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)

        self.api = self.vk.get_api()

    def run(self):
        """Run bot"""
        for event in self.long_poller.listen():
            log.info('Event - %s has occured', event.type.name)
            try:
                self.on_event(event)
            except Exception as err:
                log.error('Error during event processing')

    def on_event(self, event):
        """
        Procces event, and if its new message, send it back

        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type == VkBotEventType.MESSAGE_NEW:
            log.info('Sending message')
            self.api.messages.send(
                message=event.message.text,
                random_id=random.randint(0, 2 ** 20),
                peer_id=event.message.peer_id,
            )
        else:
            log.info('We can`t procces this event... just yet %s', event.type.name)


if __name__ == '__main__':
    configure_log()
    bot = Bot(GROUP_ID, TOKEN)
    bot.run()
