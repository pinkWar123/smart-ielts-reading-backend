from abc import ABCMeta, abstractmethod


class PasswordService(metaclass=ABCMeta):
    @staticmethod
    @abstractmethod
    def hash(password):
        pass

    @staticmethod
    @abstractmethod
    def verify(hashed_password, plain_password):
        pass
