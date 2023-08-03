import json
import time
from typing import Dict, List

import openai

import pywebio_battery
from pywebio.input import *
from pywebio.output import *
from pywebio.pin import *
from pywebio.session import set_env, download


class ChatGPTStreamResponse:
    def __init__(self, response):
        self.response = response
        self.yielded = []
        self.finish_reason = None

    def __next__(self):
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb
        chunk = next(self.response)
        self.finish_reason = chunk['choices'][0]['finish_reason']

        # { "role": "assistant" } or { "content": "..."} or {}
        delta = chunk['choices'][0]['delta']
        content = delta.get('content', '')
        if content:
            self.yielded.append(content)
        return content

    def __iter__(self):
        return self

    def result(self):
        return ''.join(self.yielded)


class ChatGPT:

    def __init__(self, messages: List[Dict] = None, model: str = "gpt-3.5-turbo", api_key=None, **model_kwargs):
        """
        Create a chatgpt client

        :param messages: A list of messages comprising the conversation so far.
          Each message is a dict with keys "role" and "content".
          See: https://platform.openai.com/docs/api-reference/chat/create#chat/create-messages
        :param model: The model to use.
        :param api_key: The openai api key.
          Get your API key from https://platform.openai.com/account/api-keys
        :param model_kwargs: Other parameters to pass to model,
          See https://platform.openai.com/docs/api-reference/chat
        """
        self._messages = list(messages or [])
        self.model_kwargs = dict(model=model, **model_kwargs)
        if api_key:
            self.model_kwargs['api_key'] = api_key

        self.pending_stream_reply: ChatGPTStreamResponse = None
        self.latest_nonstream_finish_reason = None

    def _ask(self, message: str, stream=True, **model_kwargs):
        if self.pending_stream_reply:
            self._messages.append({"role": "assistant", "content": self.pending_stream_reply.result()})
            self.pending_stream_reply = None

        self._messages.append({"role": "user", "content": message})

        resp = openai.ChatCompletion.create(
            **self.model_kwargs,
            **model_kwargs,
            messages=self._messages,
            stream=stream,
        )
        return resp

    def ask(self, message: str, **model_kwargs) -> str:
        """
        Send a message to chatgpt and get the reply in string

        :param message: The message to send
        :param model_kwargs: Other parameters to pass to openai.ChatCompletion.create()
        :return: The reply from chatgpt
        """
        resp = self._ask(message, stream=False, **model_kwargs)
        reply = resp['choices'][0]
        reply_content = reply['message']['content']
        self._messages.append({"role": "assistant", "content": reply_content})
        self.latest_nonstream_finish_reason = reply['finish_reason']

        return reply_content

    def ask_stream(self, message: str, **model_kwargs) -> ChatGPTStreamResponse:
        """
        Send a message to chatgpt and get the reply in stream

        :param message: The message to send
        :param model_kwargs: Other parameters to pass to openai.ChatCompletion.create()
        :return: A iterator that yields the reply from chatgpt.
          The iterator will be exhausted when the reply is complete.
        """
        resp = self._ask(message, stream=True, **model_kwargs)
        self.pending_stream_reply = ChatGPTStreamResponse(resp)
        return self.pending_stream_reply

    def latest_finish_reason(self) -> str:
        """The finish reason for the latest reply of chatgpt.

        The possible values for finish_reason are:
          'stop': API returned complete model output
          'length': Incomplete model output due to max_tokens parameter or token limit
          'content_filter': Omitted content due to a flag from our content filters
          'null': API response still in progress or incomplete

        See: https://platform.openai.com/docs/guides/chat/response-format
        """
        if self.pending_stream_reply:
            return self.pending_stream_reply.finish_reason
        return self.latest_nonstream_finish_reason

    def messages(self) -> List[Dict]:
        """Get all messages of the conversation """
        if self.pending_stream_reply:
            self._messages.append({"role": "assistant", "content": self.pending_stream_reply.result()})
            self.pending_stream_reply = None

        return self._messages


def get_openai_config():
    openai_config = json.loads(pywebio_battery.get_localstorage('openai_config') or '{}')
    if not openai_config:
        openai_config = input_group('OpenAI API Config', [
            input('API Key', name='api_key', type=TEXT, required=True,
                  help_text='Get your API key from https://platform.openai.com/account/api-keys'),
            input('API Server', name='api_base', type=TEXT, value='https://api.openai.com', required=True),
        ])
        openai_config['api_base'] = openai_config['api_base'].removesuffix('/v1').strip('/') + '/v1'
        pywebio_battery.set_localstorage('openai_config', json.dumps(openai_config))

    put_button('Reset OpenAI API Key', reset_openai_config, link_style=True)
    return openai_config


def reset_openai_config():
    pywebio_battery.set_localstorage('openai_config', json.dumps(None))
    toast("Please refresh the page to take effect")


def main():
    """"""
    set_env(input_panel_fixed=False, output_animation=False)
    put_markdown("""
    # ChatGPT
    A ChatGPT client implemented with PyWebIO. [Source Code](https://github.com/pywebio/PyWebIO/blob/dev/demos/chatgpt.py)
    TIPS: refresh page to open a new chat.
    """)
    put_select('model', ['gpt-3.5-turbo', 'gpt-4'], label='Model')

    openai_config = get_openai_config()

    bot = ChatGPT(api_key=openai_config['api_key'], api_base=openai_config['api_base'], model=pin.model)
    while True:
        form = input_group('', [
            input(name='msg', placeholder='Ask ChatGPT'),
            actions(name='cmd', buttons=['Send', 'Multi-line Input', 'Save Chat'])
        ])
        if form['cmd'] == 'Multi-line Input':
            form['msg'] = textarea(value=form['msg'])
        elif form['cmd'] == 'Save Chat':
            messages = [
                msg['content'] if msg['role'] == 'user' else f"> {msg['content']}"
                for msg in bot.messages()
            ]
            download(f"chatgpt_{time.strftime('%Y%m%d%H%M%S')}.md",
                     '\n\n'.join(messages).encode('utf8'))
            continue

        user_msg = form['msg']
        if not user_msg:
            continue

        put_info(put_text(user_msg, inline=True))

        with use_scope(f'reply-{int(time.time())}'):
            put_loading('grow', 'info')
            try:
                reply_chunks = bot.ask_stream(user_msg)
            except Exception as e:
                popup('ChatGPT Error', put_error(e))
                continue
            finally:
                clear()  # clear loading
            for chunk in reply_chunks:
                put_text(chunk, inline=True)
            clear()  # clear above text
            put_markdown(reply_chunks.result())

        if bot.latest_finish_reason() == 'length':
            put_error('Incomplete model output due to max_tokens parameter or token limit.')
        elif bot.latest_finish_reason() == 'content_filter':
            put_warning("Omitted content due to a flag from OpanAI's content filters.")


if __name__ == '__main__':
    from pywebio import start_server

    start_server(main, port=8080, debug=True, cdn=False)
