import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678


# HELPER SOCKET METHODS
def build_send_recv_parse(conn, code, data):
    try:
        build_and_send_message(conn, code, data)
        x = recv_message_and_parse(conn)
        return x
    except KeyboardInterrupt and ConnectionAbortedError:
        conn.close()


def build_and_send_message(conn, code, data):
    """
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), data (str)
	Returns: Nothing
	"""
    try:
        full_msg = chatlib.build_message(code, data)
        conn.send(full_msg.encode())
    except KeyboardInterrupt and ConnectionAbortedError:
        conn.close()


def recv_message_and_parse(conn):
    """
    Recieves a new message from given socket,
	then parses the message using chatlib.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message. 
	If error occured, will return None, None
	"""
    try:
        full_msg = conn.recv(1024).decode()
        cmd, data = chatlib.parse_message(full_msg)
        return cmd, data
    except KeyboardInterrupt and ConnectionAbortedError:
        conn.close()


def connect():
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connection.connect((SERVER_IP, SERVER_PORT))
    return connection


def error_and_exit(error_msg):
    return exit(error_msg)


def login(conn):
    username = input("Please enter username: \n")
    password = input("Please enter password\n")
    cerds = [username, password]
    login_connection = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["login_msg"], chatlib.join_data(cerds))
    while login_connection != ("LOGIN_OK", ""):
        print("Bad login")
        username = input("Please enter username: \n")
        password = input("Please enter password\n")
        cerds = [username, password]
        login_connection = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["login_msg"], chatlib.join_data(cerds))
    print("Logged in!")


def get_logged_users(conn):
    users = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getusers_msg"], "")
    return users


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")


def get_score(conn):
    score = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getselfscore_msg"], "")
    return score


def get_highscores(conn):
    scores = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["gethighscores_msg"], "")
    return scores


def play_question(conn):
    questionlist = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["getquestion_msg"], "")
    question = "".join(questionlist[1])
    questions = chatlib.split_data(question, question.count("#")+1)
    try:
        print("Q: " + questions[1] + ": ")
    except IndexError:
        print("The server is restarting the question DB, Hit p agin")
        return None
    for i in range(2, len(questions)-1):
        print(str(i-1) + ". " + questions[i])
    choice = input("Please enter your answer\n")
    while not choice.isdigit() or int(choice) < 1 or int(choice) > 4:
        choice = input("Please enter a valid input ")
    result = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["sendanswer_msg"], questions[0] + "#" + choice)
    if "CORRECT_ANSWER" == result[0]:
        print("You are correct! +5")
    elif "WRONG_ANSWER" == result[0]:
        print("Nope, the right answer is " + str(result[1]))
    elif "NO_QUESTIONS" == result[0]:
        print("No more questions")


def main():
    x = connect()
    login(x)
    while True:
        print("p        " + "Play a trivia question")
        print("s        " + "Get my score")
        print("h        " + "Get high score")
        print("l        " + "Get logged users")
        print("q        " + "Quit")
        y = input("Please enter your choice: ")
        if y == "p":
            play_question(x)
        elif y == "s":
            scoretup = get_score(x)
            score = "".join(scoretup[1:])
            print("Your score is: " + score)
        elif y == "h":
            print("High-Score table: \n")
            scorestup = get_highscores(x)
            scores = "".join(scorestup[1:])
            print(scores)
        elif y == "l":
            print("The logged users are:")
            users = get_logged_users(x)
            users = "".join(users[1:])
            print(users)
        elif y == "q":
            logout(x)
            break
        else:
            print("You entered a wrong input\nTry agin..")


if __name__ == '__main__':
    main()
