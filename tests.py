from unittest import TestCase
from unittest.mock import patch, Mock, ANY

from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent

from vk_bot.bot import Bot
from vk_bot.generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object': {
            'message': {
                'date': 1588707318,
                'from_id': 76993160, 'id': 23,
                'out': 0, 'peer_id': 76993160,
                'text': 'Суп', 'conversation_message_id': 23,
                'fwd_messages': [], 'important': False,
                'random_id': 0, 'attachments': [],
                'is_hidden': False
            },
            'client_info': {
                'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'open_photo'],
                'keyboard': True, 'inline_keyboard': True,
                'carousel': True, 'lang_id': 0
            }
        },
        'group_id': 194914416,
        'event_id': 'e8ee2a36f351b53850bab2f4177e7ce34a4469f4'}

    @isolate_db
    def test_run(self):
        count = 5
        obj = Mock()
        events = [obj] * count  # [obj, obj, obj, ...]
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('vk_bot.bot.vk_api.VkApi'):
            with patch('vk_bot.bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.run()

                bot.on_event.assert_called()
                bot.on_event.assert_called_with(obj)

                assert bot.on_event.call_count == count

    def test_on_event(self):
        event = VkBotMessageEvent(raw=self.RAW_EVENT)

        send_mock = Mock()

        with patch('vk_bot.bot.vk_api.VkApi'):
            with patch('vk_bot.bot.VkBotLongPoll'):
                bot = Bot('', '')
                bot.api = Mock()
                bot.api.messages.send = send_mock

                bot.on_event(event)

        send_mock.assert_called_once_with(
            message=self.RAW_EVENT['object']['message']['text'],
            random_id=ANY,
            peer_id=self.RAW_EVENT['object']['message']['peer_id'],
        )

    def test_image_generation(self):
        with open('files/avatar_test.png', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()

        with patch('request.get', return_value=avatar_mock):
            ticket_file = generate_ticket('NAME', 'EMAIL')

        with open('files/my1.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes
