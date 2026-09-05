from olist_data_platform.platform.postgres.file_hash import sha256_file


def test_sha256_file_is_stable(tmp_path) -> None:
    path = tmp_path / "sample.csv"
    path.write_bytes(b"abc\n")

    assert sha256_file(path) == (
        "edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb"
    )
