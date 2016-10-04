import socket
from json import dumps, loads


def get_local_ip():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


MESSAGE_PORT = 10000
BROADCAST_PORT = 10001


class MessageFields:
    BROKER_ADDRESS = 'broker_address'
    MESSAGE_CONTENT = 'message_content'
    MESSAGE_ID = 'message_id'
    MESSAGE_TEXT = 'message_text'
    SENDER_PORT = 'sender_port'
    SENDER_USERNAME = 'sender_username'
    RECEIVER_USERNAME = 'receiver_username'
    USER_LIST = 'user_list'


class MessageId:
    ACKNOWLEDGE_LOG_IN = 'acknowledge_log_in'
    LOG_IN = 'log_in'
    LOG_OUT = 'acknowledge_log_out'
    SEND_MESSAGE = 'send_message'
    RECEIVE_MESSAGE = 'receive_message'
    UPDATE_USER_SET = 'update_user_set'


class MessageBuilder:
    @classmethod
    def make_sendable(cls, message):
        return dumps(message)

    @classmethod
    def make_readable(cls, json_message):
        return loads(json_message)
