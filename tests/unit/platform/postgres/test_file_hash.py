from hashlib import sha256

from olist_data_platform.platform.postgres.file_hash import sha256_file


def test_sha256_file_matches_expected_digest(tmp_path) -> None:
    file_path = tmp_path / "sample.csv"
    content = b"a;b\n1;2\n"
    file_path.write_bytes(content)

    assert sha256_file(file_path) == sha256(content).hexdigest()
