import json

from belgekalkan.cli import main


def test_cli_writes_output_and_value_free_manifest(tmp_path) -> None:
    source = tmp_path / "source.txt"
    output = tmp_path / "safe.txt"
    manifest = tmp_path / "manifest.json"
    source.write_text("Ara: test@example.com", encoding="utf-8")

    assert main([str(source), "--output", str(output), "--manifest", str(manifest)]) == 0
    assert output.read_text(encoding="utf-8") == "Ara: [EMAIL]"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["finding_count"] == 1
    assert "test@example.com" not in manifest.read_text(encoding="utf-8")


def test_cli_prints_to_stdout(tmp_path, capsys) -> None:
    source = tmp_path / "source.txt"
    source.write_text("Temiz metin", encoding="utf-8")
    assert main([str(source)]) == 0
    assert capsys.readouterr().out == "Temiz metin"

