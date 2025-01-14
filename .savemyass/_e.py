import sys
import hashlib
import os

def derive_key(passphrase: str, salt: bytes, length: int) -> bytes:
    """Derive a key from passphrase using PBKDF2"""
    return hashlib.pbkdf2_hmac(
        'sha256',
        passphrase.encode(),
        salt,
        iterations=100000,
        dklen=length
    )

def xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with key (repeating key if necessary)"""
    key_len = len(key)
    return bytes(data[i] ^ key[i % key_len] for i in range(len(data)))

def encrypt(data: bytes, passphrase: str) -> bytes:
    """Encrypt data using XOR with key derived from passphrase"""
    salt = os.urandom(16)
    key = derive_key(passphrase, salt, 32)
    encrypted = xor_bytes(data, key)
    return salt + encrypted

def decrypt(data: bytes, passphrase: str) -> bytes:
    """Decrypt data using XOR with key derived from passphrase"""
    salt, encrypted = data[:16], data[16:]
    key = derive_key(passphrase, salt, 32)
    return xor_bytes(encrypted, key)

def main():
    if len(sys.argv) != 4:
        print("Usage: python _e.py [encrypt|decrypt] <file> <passphrase>")
        sys.exit(1)

    action, filepath, passphrase = sys.argv[1:4]

    with open(filepath, 'rb') as f:
        data = f.read()

    if action == 'encrypt':
        result = encrypt(data, passphrase)
    elif action == 'decrypt':
        try:
            result = decrypt(data, passphrase)
        except Exception:
            print(f"Error: Failed to decrypt {filepath}. Wrong passphrase?")
            sys.exit(1)
    else:
        print("Invalid action. Use 'encrypt' or 'decrypt'")
        sys.exit(1)

    with open(filepath, 'wb') as f:
        f.write(result)

if __name__ == '__main__':
    main()
