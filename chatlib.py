# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
	"login_msg": "LOGIN",
	"logout_msg": "LOGOUT",
	"getselfscore_msg": "MY_SCORE",
	"gethighscores_msg": "HIGHSCORE",
	"getquestion_msg": "GET_QUESTION",
	"sendanswer_msg": "SEND_ANSWER",
	"getusers_msg": "LOGGED"
}  # .. Add more commands if needed

PROTOCOL_SERVER = {
	"error_msg": "Error!",
	"login_ok_msg": "LOGIN_OK",
	"login_failed_msg": "ERROR",
	"sendscore_ok_msg": "YOUR_SCORE",
	"sendscore_faild_msg": "ERROR",
	"sendhighscores_msg": "ALL_SCORE",
	"sendhighscores_failed_msg": "ERROR",
	"getquestion_ok_msg": "YOUR_QUESTION",
	"getquestion_fail_msg": "NO_QUESTIONS",
	"sendanswer_ok_msg": "CORRECT_ANSWER",
	"sendanswer_fail_msg": "WRONG_ANSWER",
	"getusers_ok_msg": "LOGGED_ANSWER"
}  # ..  Add more commands if needed

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
	"""
	Gets command name (str) and data field (str) and creates a valid protocol message
	Returns: str, or None if error occured
	"""
	full_msg = ""
	if cmd not in PROTOCOL_CLIENT.values() and cmd not in PROTOCOL_SERVER.values():
		return ERROR_RETURN
	try:
		full_msg += cmd
		for i in range(CMD_FIELD_LENGTH - len(full_msg)):
			full_msg += " "
		full_msg += DELIMITER
		if len(data) < 10:
			for i in range(LENGTH_FIELD_LENGTH - 1):
				full_msg += str(0)
			full_msg += str(len(data))
		elif 10 <= len(data) < 100:
			for i in range(LENGTH_FIELD_LENGTH - 2):
				full_msg += str(0)
			full_msg += str(len(data))
		elif 100 <= len(data) < 1000:
			for i in range(LENGTH_FIELD_LENGTH - 3):
				full_msg += str(0)
			full_msg += str(len(data))
		elif 1000 <= len(data) <= MAX_DATA_LENGTH:
			full_msg += str(len(data))
		full_msg += DELIMITER
		full_msg += data
		return full_msg
	except TypeError:
		return ERROR_RETURN


def parse_message(data):
	"""
	Parses protocol message and returns command name and data field
	Returns: cmd (str), data (str). If some error occured, returns None, None
	"""
	# Implement code ...

	# The function should return 2 values
	if data.count(DELIMITER) != 2:
		return ERROR_RETURN, ERROR_RETURN
	data = data.split(DELIMITER)
	data[0] = data[0].replace(" ", "")
	if not data[1].replace(" ", "").isdigit():
		return ERROR_RETURN, ERROR_RETURN
	elif int(data[1].replace(" ", "")) != len(data[2]) and data[2] is not None:
		return ERROR_RETURN, ERROR_RETURN
	elif data[0] not in PROTOCOL_CLIENT.values() and data[0] not in PROTOCOL_SERVER.values():
		return ERROR_RETURN, ERROR_RETURN
	else:
		data[0] = data[0].replace(" ", "")
		data.pop(1)
		return tuple(data)


def split_data(msg, expected_fields):
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns None
	"""
	newmsg = msg.split("#")
	if len(newmsg) == expected_fields:
		return newmsg
	else:
		return ERROR_RETURN


def join_data(msg_fields):
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
	Returns: string that looks like cell1#cell2#cell3
	"""
	try:
		joined_string = "#".join(msg_fields)
		return joined_string
	except TypeError:
		return ERROR_RETURN
