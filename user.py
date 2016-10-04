from connection import Connection


class SenderReceiver():
    def __init__(self):
        self.writing_connection = Connection(read=False)
        self.reading_connection = Connection(read=True)

        message = self.send_login_message()
        print(message)

    def send_login_message(self):
        self.writing_connection.broadcast_message('mihai, ' +  str(self.reading_connection.get_reading_port()))
        broker_message = self.reading_connection.receive_message()
        return broker_message

