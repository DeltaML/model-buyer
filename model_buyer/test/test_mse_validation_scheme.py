import numpy as np
from commons.encryption.encryption_service import EncryptionService


def test_mse_validation_scheme():
    encryption_service = EncryptionService(is_active=True)
    public_key, private_key = encryption_service.generate_key_pair(1024)
    encryption_service.set_public_key(public_key.n)

    # Actor 1 - First step - generating the serialized encrypted array with noise
    # Sending the array to Actor 2
    array = np.asarray([34.0, 56.0, 1.1, 0.56, 88.9, 0.112, 22.13])
    noise = np.random.randint(array.min(), array.max(), (1, array.size))[0]
    encrypted_noised_array = encryption_service.encrypt_collection(array + noise)
    serialized_encrypted_noised_array = encryption_service.get_serialized_collection(encrypted_noised_array)

    # Actor 2 - Second step - deserializing and decrypting the array with noise received from Actor 1
    # Sending the array to Actor 1
    deserialized_encrypted_noised_array = encryption_service.get_deserialized_collection(serialized_encrypted_noised_array)
    deserialized_decrypted_noised_array = encryption_service.decrypt_collection(deserialized_encrypted_noised_array)

    # Actor 1 - Third step - Using the decrypted array, removing the noise, calculates the square of
    # each component and then the mean of the array
    # Sending the value and the noise to Actor 2 for validation
    noised_array = np.asarray(deserialized_decrypted_noised_array)
    array2 = noised_array - noise
    value = np.mean(array2 ** 2)

    # Actor 2 - Fourth step - Substracting noise from decrypted array, doing same calculation that Actor 1
    # Validating value sent by Actor 1 with value calculated here
    noised_array2 = np.asarray(deserialized_decrypted_noised_array)
    array3 = noised_array2 - noise
    value2 = np.mean(array3 ** 2)

    assert value == value2
    assert value == np.mean(array ** 2)


test_mse_validation_scheme()
