
from sys import exit, argv
from socket import *

user_messages = {}


def store_requests(user_name, receiver_name, message):
    if receiver_name not in user_messages:
        user_messages[receiver_name] = []
    user_messages[receiver_name].append((user_name, message))
    print(f"Here is the message: {message}")
    

def create_response(user_name):
    MagicNo = 0xAE73
    messages = []
    for sender_name, message in user_messages.items():
        messages.extend(message)

    num_items = len(messages)
    more_msgs = 0
    if num_items > 255:
        num_items = 255
        more_msgs = 1
    
    response = bytearray([(MagicNo >> 8), (MagicNo & 0xFF), 3, num_items, more_msgs])

    for i in range(num_items):
        sender, message = messages[i]
        SenderLen = len(sender)
        MessageLen = len(message)
        response.extend([SenderLen, (MessageLen >> 8) & 0xFF, MessageLen & 0xFF])
        response.extend(sender.encode("UTF-8"))
        response.extend(message.encode("UTF-8"))

    return response
    

def main():
    sock = None
    conn = None

    try:
        if len(argv) != 2:
            print(f"Usage:\n\n\tpython(3) {argv[0]} <port>\n")
            exit()
            
        port = int(argv[1])

        if port < 1024 or port > 64000:
            print("Port number must be between 1024 and 64000")
            exit()

        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(5)

        while True:

            conn, client = sock.accept()
            print("IP of client: ", client[0], "\nPort Number: ", client[1])


            try:
                fixed_header = conn.recv(7)
                MagicNo = (fixed_header[0] << 8) + fixed_header[1]
                Id = fixed_header[2]

                
                if MagicNo != 0xAE73:
                    raise ValueError("Magic Number wrong")

                if Id == 1:
                    response = create_response(user_name)
                    
                    conn.send(response)
                
                elif Id == 2:
                    NameLen = fixed_header[3]
                    ReceiverLen = fixed_header[4]
                    MessageLen = (fixed_header[5] << 8) + fixed_header[6]
                    user_name = conn.recv(NameLen).decode("UTF-8")
                    receiver_name = conn.recv(ReceiverLen).decode("UTF-8")
                    message = conn.recv(MessageLen).decode("UTF-8")
                    store_requests(user_name, receiver_name, message)

                else:
                    raise ValueError("Id wrong")

            except sock.timeout:
                print("Socket timed out, closing connection")
                sock.close()
                
            finally:
                if conn != None:
                    conn.close()

    except UnicodeDecodeError: 
        print("ERROR: Decoding/encoding failure")

    except ValueError:
        print(f"ERROR: Port ’{argv[2]}’ is not an integer")

    except OSError as err: 
        print(f"ERROR: {err}") 

    finally:
        if sock != None:
            sock.close()
            
main()

