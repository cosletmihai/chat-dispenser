import socket
from json import dumps


def get_local_ip():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


MESSAGE_PORT = 10000
BROADCAST_PORT = 10001


class MessageField:
    MESSAGE_ID = 'message_id'
    SENDER_USERNAME = 'sender_username'
    RECEIVER_USERNAME = 'receiver_username'
    MESSAGE_CONTENT = 'message_content'
    USER_SET = 'ids_set'


class MessageID:
    LOG_IN = 'log_in'
    ACKNOWLEDGE_LOG_IN = 'acknowledge_log_in'
    UPDATE_USER_SET = 'update_user_set'
    LOG_OUT = 'acknowledge_log_out'


class MessageBuilder:
    def make_sendable(self, message):
        json_to_send = dumps(message)
        return json_to_send.encode('utf-8')