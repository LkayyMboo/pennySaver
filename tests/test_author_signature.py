from app.author_signature import decode_author_signature

def test_signature_decodes_exactly():
    assert decode_author_signature() == "Lindokuhle Blesseth Mbokazi"
