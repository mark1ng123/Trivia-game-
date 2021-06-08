##############################################################################
# server.py
##############################################################################

import socket
import chatlib
import select
import random
import json
import requests
import html

# GLOBALS
users = {
    "Mark": {"password": "123", "score": "0", "questions_asked": ""},
    "Adi": {"password": "123", "score": "0", "questions_asked": ""},
}
questions = {}

logged_users = {}  # a dictionary of client hostnames to usernames - will be used later

messages_to_send = []

questionIndex = []

data = questions.values()
keys = questions.keys()
question_data = []
question_keys = []

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS
def reload_data():
    global question_data
    global question_keys

    for quest in data:
        question_data.append(quest)

    for key in keys:
        question_keys.append(key)


def load_questions_from_web():
    response = requests.get("https://opentdb.com/api.php?amount=50&type=multiple")
    content = response.content
    data = json.loads(content)
    randomAnswerIndex = randint(1, 4)
    for index, row in enumerate(data["results"]):
        data_list = []
        data_list.append(html.unescape(row["question"]))
        for inc_answer in row["incorrect_answers"]:
            data_list.append(html.unescape(inc_answer))
        data_list.insert(randomAnswerIndex, html.unescape(row["correct_answer"]))
        data_list.append(str(randomAnswerIndex))
        questions[str(index + 1)] = data_list


def build_and_send_message(conn, code, msg):
    # copy from client
    try:
        full_msg = chatlib.build_message(code, msg)
        conn.send(full_msg.encode())
        print("[SERVER] ", full_msg)  # Debug print
    except KeyboardInterrupt and ConnectionAbortedError and TypeError:
        handle_logout_message(conn)


def recv_message_and_parse(conn):
    # copy from client
    try:
        full_msg = conn.recv(1024).decode()
        cmd, data = chatlib.parse_message(full_msg)
        print("[CLIENT] ", full_msg)  # Debug print
        return cmd, data
    except KeyboardInterrupt and ConnectionAbortedError and TypeError:
        handle_logout_message(conn)
        return None


def create_random_question():
    global question_data
    global keys
    global data

    if len(question_data) == 0:
        reload_data()
    randomIndex = random.randint(0, len(data) - 1)
    randomQuestion = question_data[randomIndex]
    question_data.pop(randomIndex)
    randomKey = question_keys[randomIndex]
    question_keys.pop(randomIndex)
    randomQuestion = chatlib.join_data(randomQuestion)
    randomQuestion = str(randomKey) + "#" + randomQuestion
    return randomQuestion


# Data Loaders #
def load_questions():
    """
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Recieves: -
	Returns: questions dictionary
	"""
    return questions


def load_user_database():
    """
	Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
	Recieves: -
	Returns: user dictionary
	"""
    return users


# SOCKET CREATOR

def setup_socket():
    """
	Creates new listening socket and returns it
	Recieves: -
	Returns: the socket object
	"""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen()
    return server_sock


def send_error(conn, error_msg):
    """
	Send error message with given message
	Recieves: socket, message error string from called function
	Returns: None
	"""
    error_msg = ERROR_MSG + error_msg
    conn.send(error_msg.encode())


# MESSAGE HANDLING
def handle_getscore_message(conn, username):
    global users
    score = users[username]["score"]
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["sendscore_ok_msg"], score)


def handle_highscores_messsage(conn):
    global users
    global logged_users
    scores = []
    for user in users:
        scores.append(str(user) + ": " + str(users[user]["score"]))
    scores = sorted(scores, reverse=True)
    scores = chatlib.join_data(scores)
    scores = scores.replace("#", "\n")
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["sendhighscores_msg"], scores)


def handle_question_message(conn):
    quest = create_random_question()
    if quest is None:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["getquestion_fail_msg"], "")
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["getquestion_ok_msg"], quest)


def handle_answer_message(conn, username, answer):
    answer = chatlib.split_data(answer, 2)
    answerIndex = answer[0]
    questionAnswer = questions[answerIndex][5]
    currentScore = int(users[username]["score"])
    if answer[1] == questionAnswer:
        finalScore = currentScore + 5
        users[username]["score"] = str(finalScore)
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["sendanswer_ok_msg"], "")
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["sendanswer_fail_msg"], questionAnswer)


def handle_logged_message(conn):
    connectedUserslst = logged_users.values()
    connectedUsers = ",".join(connectedUserslst)
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["getusers_ok_msg"], connectedUsers)


def handle_logout_message(conn):
    """
	Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
	Recieves: socket
	Returns: None
	"""
    global logged_users
    print("[CLIENT]" + str(conn.getpeername()) + " disconnected")
    logged_users.pop(str(conn.getpeername()))
    conn.close()


def handle_login_message(conn, data):
    """
	Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Recieves: socket, message code and data
	Returns: None (sends answer to client)
	"""
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later
    INFO = chatlib.split_data(data, 2)
    while INFO[0] not in users.keys() or INFO[1] not in users[INFO[0]].values():
        if INFO[0] in users.keys() and INFO[1] not in users[INFO[0]].values():
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], "Password is incorrect")
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_failed_msg"], "User does not exist")
        cmd, data = recv_message_and_parse(conn)
        INFO = chatlib.split_data(data, 2)
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
    logged_users[str(conn.getpeername())] = INFO[0]


def handle_client_message(conn, cmd, data):
    """
	Gets message code and data and calls the right function to handle command
	Recieves: socket, message code and data
	Returns: None
	"""
    global logged_users
    if str(conn.getpeername()) not in logged_users.keys():
        if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
            handle_login_message(conn, data)
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], "")
    else:
        if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
            handle_logout_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["getselfscore_msg"]:
            data = logged_users.get(str(conn.getpeername()))
            handle_getscore_message(conn, data)
        elif cmd == chatlib.PROTOCOL_CLIENT["gethighscores_msg"]:
            handle_highscores_messsage(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["getusers_msg"]:
            handle_logged_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["getquestion_msg"]:
            handle_question_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["sendanswer_msg"]:
            handle_answer_message(conn, logged_users[str(conn.getpeername())], data)


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions
    global messages_to_send

    load_questions_from_web()
    create_random_question1()
    SERVER_SOCKET = setup_socket()
    client_sockets = []
    while True:
        ready_to_read, ready_to_write, in_error = select.select([SERVER_SOCKET] + client_sockets, client_sockets, [])
        for currentsocket in ready_to_read:
            if currentsocket is SERVER_SOCKET:
                (client_socket, client_adress) = currentsocket.accept()
                print("New connection was made by: " + str(client_adress))
                client_sockets.append(client_socket)
                print("Listening For New Data from clients: ")
            else:
                try:
                    cmd, data = recv_message_and_parse(currentsocket)
                    handle_client_message(currentsocket, cmd, data)
                    if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                        client_sockets.remove(currentsocket)
                    elif (cmd, data) == (None, None):
                        handle_logout_message(currentsocket)
                        client_sockets.remove(currentsocket)
                    print("Listening For New Data from clients: ")
                except KeyboardInterrupt and ConnectionAbortedError:
                    print("Remote user disconnected forcelly...")
                    if currentsocket.getpeername() in logged_users:
                        handle_logout_message(currentsocket)
                        client_sockets.remove(currentsocket)
                    else:
                        client_sockets.remove(currentsocket)
                        currentsocket.close()

        for message in messages_to_send:
            client_socket, cmd, data = message
            client_socket.send(data.encode())
            if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                client_sockets.remove(client_socket)
                client_socket.close()
            messages_to_send.remove(message)


if __name__ == '__main__':
    main()
