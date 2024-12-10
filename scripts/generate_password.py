import hashlib
import json
import secrets


def generate_hashed_password(username, password):
    # Generate a random salt
    salt = secrets.token_hex(16)

    # Hash the password with salt
    salted = (password + salt).encode("utf-8")
    password_hash = hashlib.sha256(salted).hexdigest()

    # Create users dictionary
    users = {username: {"hash": password_hash, "salt": salt}}

    # Convert to JSON string
    return json.dumps(users)


# Example usage:
username = "anton"
password = "Anton123"
users_json = generate_hashed_password(username, password)
print(f"Set this as your 'users' environment variable:")
print(users_json)
