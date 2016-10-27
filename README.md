## Message Agent

#### Laboratory Purpose
An agent-based messaging *app* that would allow asynchronous communication between the **components** of a `distributed system`.


#### Generic Requirements and Objectives
 - Use `UDP` protocol for `unicast` and `multicast` transmission.
 - Use `TCP` protocol for data transmission.
 - Analyze and process collections of objects.

![alt text](http://i.imgur.com/5UqlgKl.png "Project Structure") <br>
*Basic structure of the distributed messanging app*

The above structure represents an oversimplified version of what I set my mind to do.
In my app the *Sender* and the *Receiver* are **one**. So my app has 2 distinct entites, if I may say so:
- the `Broker` - the main *star* of the show.
  - It keeps track of the users currently online (**TODO**: implement a feature that removes users if they sign out or they are inactive for a longer period of time)
  - It *redirects* the messages to the correct destination
- the `Sender/Receiver` - it is a client that allows for sending and receiving messages

#### Project Structure
In order to send messages I decided to stick with the already available `socket`s in `python` (I decided to use Python as my language of choice), and not a third party library (like `twisted`) as it would have taken too much time to learn it, and I didn't need any complicated features to send some messages over a local network. But, still, I decided to add a layer of *abstraction* over the I/O module.

The `connection.py` file contains two classes:
- `SocketCreation` - the class that allows for creating and configuring `UDP` sockets
- `Connection` - the class that I use to interface the communication methods like:
  - broadcasting a message
  - sending an unicast message
  - receiving a message
  - getting info about the `socket` that is used for the communication
  - encoding/decoding messages

The `utils.py`, a file that is present in almost all my projects, contains useful `constants`, `functions`, or `classes`. In this case it contains:
- `get_local_ip` - a function for getting the `local ip`
- ports used for sending messages
- constants for the structure of the messages sent (and received, obviously) in the app
- `DebugMessage` - a class that allows for more insightful message debugging
- `MessageBuilder` - a class that transforms `dict`s, a python *data structure* into `json`s, thus preparing it for sending it

The `broker.py` file, as stated before, *the star of the show*, handles the core of the messaging app.
Each `Broker` object has `3` **connections** (well, `socket`s really, but with added interfaces from the `Connection` class):
- a *writing* one - for sending messages
- a *reading* one - for listening and receiving messages
- a listening for a *broadcast* one - that listens for new `users` that come online.
In order to implement threading in the program, I decided to use python's `selectors` module.
> This module allows high-level and efficient I/O multiplexing, built upon the `select` module primitives. Users are encouraged to use this module instead, unless they want precise control over the OS-level primitives used.

And since I didn't really need *precise control over the OS-level primitives used* I used it, instead of the `select` one. Each of the listening `connection`s is registered on the selector with the following pattern:
```python
selector = selectors.DefaultSelector()
selector.register(<file object>, # like a socket
                  selectors.EVENT_READ, # the type of event read/write
                  <function>) # to handle what happens when the event gets triggered
```

`_process_login` - `method` that handles what happens when the `broadcasting` socket receives a message by adding the connection to the `user_list` and sending back an `ack` message that the connection went through. <br>

`_process_receive` - handles the other listening socket events, by understanding what the `broker` needs to do with the receiving message. Now it just "*redirects*" the message to the destination user. <br>
(**TODO**: implement commands like: `get_user_list`, `multicast_message` or `broadcast_message`)

`send_message` - well, as the name says (as method naming is crucial for a good system) it sends messages.

The `user.py` file handles how the user interacts with the system. It contains useful info about the user
and has `2` `connections`, one for writing and another for reading.
It can read and write messages from other users (and at the moment from himself - you can send yourself messages if you don't have any friends to write to).

I have decided to encode my messages using the `JSON` format, as it's very modular and easy to read.
For easyness' sake I've created 2 helper `Classes` that define the possible **message fields** and **message types**:
```python
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
```

Each JSON message contains `2` fields which are always present:
- the `message id` which can be one of from the `MessageID` class
- the `message content` which can contain fields from the `MessageField` class

A message can look like this:
```json
{
  "message_id": "log_in",
  "message_content": {
    "sender_port": 41796,
    "sender_username": "mihai"
  }
}
```

But it can vary a lot depending on the type of message sent.

To explain the structure and relationship of the Broker - Sender/Receiver I would use the following image:

![Message System](http://i.imgur.com/FdpoHNl.png "Message Relaying") <br>
*This is the main path of the messages*

As an improvement, besides the facts I mentioned above I would implement a `Dead Letter Channel`

![Dead Letter Channel](http://i.imgur.com/C9mMSWE.png "Message Relaying") <br>
So that we don't lose important cat pictures or funny joke messages due to unreliable broker activity.


#### Conclusion
I had a lot of fun working on the laboratory work as it allowed me to try out (and remind myself that network programming is extremely fun) new methods of communication (not that I discovered them, but I used them for the first time)

#### Bibliography
- https://docs.python.org/3/library/socket.html
- https://docs.python.org/3/library/selectors.html
- http://www.enterpriseintegrationpatterns.com/patterns/messaging/MessagingChannelsIntro.html (read very little from here)
