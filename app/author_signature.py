import base64

# Author signature: reversible Base64 encoding (NOT encryption) of the author's full name.
AUTHOR_SIGNATURE_B64 = "TGluZG9rdWhsZSBCbGVzc2V0aCBNYm9rYXpp"


def decode_author_signature() -> str:
    return base64.b64decode(AUTHOR_SIGNATURE_B64).decode("utf-8")
