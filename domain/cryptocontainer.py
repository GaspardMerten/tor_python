from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

ENCRYPTED_SYM_KEY_LENGTH_HEX = 512


class CryptoContainer:
    """
        A class to help with encryption and decryption of messages using private and public keys pair.
    """

    def __init__(self, public_key_path=None, private_key_path=None):
        """
            Creates a new CryptoContainer object.
            If public_key_path and private_key_path are not provided, a new key pair will be generated.
        """

        if public_key_path and private_key_path:
            public_key_bytes = open(public_key_path, "rb").read()
            private_key_bytes = open(private_key_path, "rb").read()
        else:
            public_key_bytes, private_key_bytes = _generate_public_and_private_key_pair()

        self.private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )
        self.public_key = serialization.load_pem_public_key(
            public_key_bytes,
            backend=default_backend()
        )

    def get_public_key_bytes(self) -> bytes:
        """
            Returns the public key of this CryptoContainer as bytes.
        """
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def encrypt(self, message):
        """
            Encrypts the given message using the public key of this CryptoContainer.
        """
        return _encrypt_message_using_sha256(message, self.public_key)

    def decrypt(self, message) -> Tuple[str, str]:
        return decrypt_message_using_sha256(
            message,
            self.private_key
        )


def encrypt_message_using_public_key(message: str, public_key: bytes) -> Tuple[str, bytes]:
    # load public key from pem format key

    public_key_rsa = serialization.load_pem_public_key(public_key, backend=default_backend())

    return _encrypt_message_using_sha256(message, public_key_rsa)


def generate_symmetric_key():
    return Fernet.generate_key()


def _encrypt_message_using_sha256(message: str, public_key: RSAPublicKey) -> Tuple[str, bytes]:
    """
        Starts by generating a symmetric key, encrypts it using the public key provided
        and then encrypts the message using the symmetric key.
    """
    sym_key = generate_symmetric_key()

    sym_key_message_part = public_key.encrypt(sym_key, padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    ))

    encrypted_message = Fernet(sym_key).encrypt(bytes(message, "utf-8"))

    return sym_key_message_part.hex() + encrypted_message.decode("utf-8"), sym_key


def decrypt_message_using_sha256(message: str, private_key) -> Tuple[str, str]:
    """
        Decrypts the given message using the given private key.
        It first decrypts the symmetric key and then decrypts the message using the symmetric key.
    """
    encrypted_sym_key = bytes.fromhex(message[:ENCRYPTED_SYM_KEY_LENGTH_HEX])

    sym_key = private_key.decrypt(
        encrypted_sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return Fernet(sym_key).decrypt(message[ENCRYPTED_SYM_KEY_LENGTH_HEX:].encode()).decode("utf-8"), sym_key


def _generate_public_and_private_key_pair(bits=2048):
    """
        Generates a new public and private key pair.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=bits,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ), private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
