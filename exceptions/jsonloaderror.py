class JsonLoadError(Exception):
    def __init__(self, user_message: str):
        self.user_message = user_message
