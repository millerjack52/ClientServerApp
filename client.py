import sys
import socket


def create_request(user_name):
    message_check = False
    while not message_check:
        message = input("Please enter a message to send: ")
        message = message.encode("UTF-8")
        if len(message) < 1 or len(message) > 65535:
            print("Message needs to contain at least 1 character and less than 65535 bytes")
        else:
            message_check = True

    receiver_check = False
    while not receiver_check:
        receiver_name = input("Please enter the name of the receiver: ")
        receiver_name = receiver_name.encode("UTF-8")
        if len(receiver_name) < 1 or len(receiver_name) > 255:
            print("Receiver name must be between 1 and 255 bytes")
        else:
            receiver_check = True
    
    NameLen = len(user_name)
    ReceiverLen = len(receiver_name)
    MessageLen = len(message)
    
    record = bytearray([(0xAE73 >> 8), (0xAE73 & 0xFF), 2, NameLen, ReceiverLen, (MessageLen >> 8), (MessageLen & 0xFF)])
    record.extend(user_name)
    record.extend(receiver_name)
    record.extend(message)
    return record

def read_response(sock, user_name):
    try:
        fixed_header = sock.recv(5)
        MagicNo = (fixed_header[0] << 8) + fixed_header[1]
        Id = fixed_header[2]
        NumItems = fixed_header[3]
        MoreMsgs = fixed_header[4]

        if MagicNo != 0xAE73:
            raise ValueError("The magic number is not 0xAE73")
        if Id != 3:
            raise ValueError("The ID value is not 3")
        if MoreMsgs < 0 or MoreMsgs > 1:
            raise ValueError("MoreMsgs value is not 0 or 1")

        
        for i in range(NumItems):
            packet_header = sock.recv(3)
            SenderLen = packet_header[0]
            MessageLen = (packet_header[1] << 8) + packet_header[2]
            sender = sock.recv(SenderLen).decode("UTF-8")

            message = sock.recv(MessageLen).decode("UTF-8")
            if sender == user_name.decode("UTF-8"):
                print("Sender:", sender)
                print("Message:", message)
        
    except Exception as e:
        raise ValueError("Error reading response: " + str(e))

def main():
    sock = None

    try:
        if len(sys.argv) != 5:
            print(f"Usage:\n\ntpython(3) {sys.argv[0]} <hostname> <port> <user name> <request type>\n")
            sys.exit()

        host_name = sys.argv[1]
        port = int(sys.argv[2])
        user_name = sys.argv[3]
        request_type = sys.argv[4]
        user_name = user_name.encode("UTF-8")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host_name, port))

        
        if request_type == "create":
            record = create_request(user_name)
            sock.send(record)
            
        elif request_type == "read":
            NameLen = len(user_name)
            ReceiverLen = 0
            read_request = bytearray([0xAE73 >> 8, 0xAE73 & 0xFF, 1, NameLen, ReceiverLen, 0, 0])
            sock.send(read_request)
            read_response(sock, user_name)

    except UnicodeDecodeError:
        print("ERROR: Response decoding failure")

    except ValueError as ve:
        print("ERROR:", ve)

    except socket.gaierror:
        print(f"ERROR: Host '{host_name}' does not exist")

    except OSError as err:
        print(f"ERROR: {err}")

    finally:
        if sock is not None:
            sock.close()


main()