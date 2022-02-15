# Although we are using NoSQL,
# this file is used for validating data entry or pack them as json object.
# Example below:

class User:
    def __init__(self, email, password, auth_type):
        self.email = email
        self.password = password,
        self.auth_type = auth_type

    def to_json(self):
        return self.__dict__
