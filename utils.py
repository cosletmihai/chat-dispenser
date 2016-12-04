import socket
from collections import namedtuple
from json import dumps, loads


def get_local_ip():
    return [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]


MESSAGE_PORT = 10000
BROADCAST_PORT = 10001


User = namedtuple('user', ['ip', 'port', 'is_online'])


class MessageFields:
    BROKER_ADDRESS = 'broker_address'
    MESSAGE_CONTENT = 'message_content'
    MESSAGE_ID = 'message_id'
    MESSAGE_TEXT = 'message_text'
    SENDER_PORT = 'sender_port'
    SENDER_USERNAME = 'sender_username'
    RECEIVER_USERNAME = 'receiver_username'
    USER_LIST = 'user_list'
    GROUP_NAME = 'group_name'
    GROUP_MEMBERS = 'group_members'


class MessageId:
    ACKNOWLEDGE_LOG_IN = 'acknowledge_log_in'
    LOG_IN = 'log_in'
    ACK_LOG_OUT = 'acknowledge_log_out'
    SEND_MESSAGE = 'send_message'
    RECEIVE_MESSAGE = 'receive_message'
    ONLINE_USERS = 'online_users'
    UPDATE_USER_SET = 'update_user_set'

    # Commands
    GET_ONLINE_USERS = 'get_online_users'
    CREATE_GROUP = 'create_group'
    GROUP_MESSAGE = 'group_message'
    LOG_OUT = 'log_out'


class DebugMessage:
    @classmethod
    def debug(cls, message, addr=None):
        if addr:
            print("from", addr)
        print(MessageFields.MESSAGE_ID, message.get(MessageFields.MESSAGE_ID))
        print(MessageFields.MESSAGE_CONTENT, message.get(MessageFields.MESSAGE_CONTENT))
        print()


class MessageBuilder:
    @classmethod
    def make_sendable(cls, message):
        return dumps(message)

    @classmethod
    def make_readable(cls, json_message):
        return loads(json_message)
