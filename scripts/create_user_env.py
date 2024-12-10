import hashlib
import json
import secrets
import getpass


def hash_password(password, salt):
    salted = (password + salt).encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def create_user_credentials():
    print("\n=== User Credentials Generator ===")

    # Get username
    username = input("\nEnter username: ").strip()
    while not username:
        print("Username cannot be empty!")
        username = input("Enter username: ").strip()

    # Get password (hidden input)
    password = getpass.getpass("Enter password: ")
    while not password:
        print("Password cannot be empty!")
        password = getpass.getpass("Enter password: ")

    # Confirm password
    confirm_password = getpass.getpass("Confirm password: ")
    while password != confirm_password:
        print("Passwords don't match! Try again.")
        password = getpass.getpass("Enter password: ")
        confirm_password = getpass.getpass("Confirm password: ")

    # Generate salt and hash password
    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)

    # Create users dictionary
    users = {username: {"hash": password_hash, "salt": salt}}

    # Convert to JSON string
    return json.dumps(users)


if __name__ == "__main__":
    try:
        users_json = create_user_credentials()
        print("\n=== Generated Environment Variable ===")
        print("\nAdd this as your 'users' environment variable in Lambda:")
        print(users_json)
        print("\nDone! ✨")
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
