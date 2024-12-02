from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os
# path  RSA Key Pair
PRIVATE_KEY_PATH = os.path.join(os.getcwd(), 'keys', 'private_key.pem')
PUBLIC_KEY_PATH = os.path.join(os.getcwd(), 'keys', 'public_key.pem')

with open(PRIVATE_KEY_PATH, 'rb') as private_file:
    private_key = serialization.load_pem_private_key(
        private_file.read(),
        password=None,
    )

with open(PUBLIC_KEY_PATH, 'rb') as public_file:
    public_key = serialization.load_pem_public_key(
        public_file.read(),
    )