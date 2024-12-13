from ollama import chat
from ollama import ChatResponse

class LlamaChat:
    def __init__(self, model=''):
        self.model = model

    def get_response(self, message):
        response: ChatResponse = chat(model=self.model, messages=[
            {
                'role': 'user',
                'content': message,
            },
        ])
        return response

    def print_response(self, message):
        response = self.get_response(message)
        return response.message.content
