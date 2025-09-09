from flask_login import UserMixin

class User(UserMixin):
    """
    User model for Flask-Login.
    """
    def __init__(self, id, email, role):
        """
        Initializes a User object.

        Args:
            id (int): The user's ID.
            email (str): The user's email address.
            role (str): The user's role (e.g., 'admin', 'user').
        """
        self.id = id
        self.email = email
        self.role = role
        # The username is derived from the email address.
        self.username = email.split('@')[0]
