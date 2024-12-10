import base64
import hashlib
import json
import os


def decode_auth_token(auth_token):
    try:
        # Remove 'Basic ' prefix from auth token
        encoded_str = auth_token.replace("Basic ", "")
        # Decode base64 string
        decoded_bytes = base64.b64decode(encoded_str)
        decoded_str = decoded_bytes.decode("utf-8")
        # Split username and password
        username, password = decoded_str.split(":")
        return {"username": username, "password": password}
    except:
        return None


def hashed_password(password, salt):
    # Combine password with salt and hash
    salted = (password + salt).encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def load_configuration():
    try:
        # Load and parse the JSON-encoded users from environment variable
        users_json = os.environ.get("users", "{}")
        users = json.loads(users_json)

        # Get the first (and only) user's credentials
        username = next(iter(users.keys()))
        password_hash = users[username]["hash"]
        salt = users[username]["salt"]

        return {"username": username, "password_hash": password_hash, "password_salt": salt}
    except:
        # Return empty config if environment variable is not set or invalid
        return {"username": "", "password_hash": "", "password_salt": ""}


UNAUTHORIZED_RESPONSE = {
    "status": "401",
    "statusDescription": "Unauthorized",
    "headers": {"www-authenticate": [{"key": "WWW-Authenticate", "value": "Basic"}]},
}


def handler(event, context):
    request = event["Records"][0]["cf"]["request"]

    # Check if authorization header exists
    if "authorization" not in request["headers"]:
        return UNAUTHORIZED_RESPONSE

    authorization_token = request["headers"]["authorization"][0]["value"]

    # Decode credentials
    credentials = decode_auth_token(authorization_token)
    if credentials is None:
        return UNAUTHORIZED_RESPONSE

    config = load_configuration()

    username = credentials["username"]
    password_hash = hashed_password(credentials["password"], config["password_salt"])

    # Verify credentials
    if username != config["username"] or password_hash != config["password_hash"]:
        return UNAUTHORIZED_RESPONSE

    return request
