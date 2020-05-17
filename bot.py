import random
import logging

import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from vk_bot import handlers
from vk_bot.models import UserState, Registration

try:
    import vk_bot.settings as settings
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


# class UserState:
#     """
#     Состояние пользователя внутри сценария
#     """
#     def __init__(self, scenario_name, step_name, context=None):
#         self.scenario_name = scenario_name
#         self.step_name = step_name
#         self.context = context or {}

class Bot:
    """
    Conf Registration by vk.com scenario
    Used Python 3.7

    Answers questions about date, place and registration
    -asks name
    -asks email
    -succesfull registration message
    if steps fails asks clarifying question until it completes
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

    @db_session
    def on_event(self, event):
        """
        Procces event, and if its new message, send it back

        :param event: VkBotMessageEvent object
        :return: None
        """
        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('We can`t procces this event... just yet %s', event.type.name)
            return

        user_id = event.message.peer_id
        text = event.message.text

        state = UserState.get(user_id=str(user_id))

        if state is not None:
            # continue scenario
            text_to_send = self.continue_scenario(event.message.text, state, user_id)
        else:
            # search intent
            for intent in settings.INTENTS:
                log.debug(f'User gets {intent}')
                if any(token in text.lower() for token in intent['tokens']):
                    # run intent
                    if intent['answer']:
                        text_to_send = intent['answer']
                        self.send_text(text_to_send, user_id)
                    else:
                        self.start_scenario(user_id, intent['scenario'], text)
                    break
            else:
                text_to_send = settings.DEFAULT_ANSWER
                self.send_text(text_to_send, user_id)




    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'

        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )


    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]

        self.send_step(step, user_id, text, context={})

        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        # continue scenario
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context):
            # next step
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                log.info('Registered: {name} {email}'.format(**state.context))
                Registration(name=state.context['name'], email=state.context['email'])
                state.delete()
        else:
            # retry current step
            self.send_step(step, user_id, step['failure_text'], state.context)


if __name__ == '__main__':
    configure_log()
    bot = Bot(settings.GROUP_ID, settings.TOKEN)
    bot.run()
