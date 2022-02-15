from .base_object import BaseObject
from passlib.hash import pbkdf2_sha256 as sha256


class User(BaseObject):
    __table_name__ = 'login_user'
    def __init__(self, attrs: dict = None):
        super().__init__(attrs)

    def set_user(self, table_objs, attrs: dict):
        self.set_attrs_by_table_class(table_objs.get(self.__table_name__), 
                                     attrs)

    # @classmethod
    # def find_by_username(cls, username):
    #     return 

    @staticmethod
    def generate_hash(password):
        return sha256.hash(password)

    @staticmethod
    def verify_hash(password, hash):
        return sha256.verify(password, hash)
