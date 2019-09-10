import numpy as np


class EncrypterWrapper(object):
    def __init__(self, encryption_service):
        self.encrypter = encryption_service

    def decrypt_number(self, number):
        if self.encrypter.is_active:
            return self.encrypter.get_deserialized_desencrypted_value(number)
        else:
            return number

    def decrypt_collection(self, collection):
        private_key = self.encrypter.get_private_key()
        if self.encrypter.is_active:
            collection = self.encrypter.decrypt_and_deserizalize_collection(private_key, collection)
        return np.asarray(collection)

    def only_serialize_collection(self, collection):
        if self.encrypter.is_active:
            return self.encrypter.get_serialized_collection(collection)
        else:
            return collection

    def only_serialize_encrypted_collection(self, collection):
        if self.encrypter.is_active:
            return self.encrypter.get_serialized_encrypted_collection(collection)
        else:
            return collection
