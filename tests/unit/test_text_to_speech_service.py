"""services/text_to_speech_service.py: conversão de áudio para formato compatível com o
Telegram, com a ferramenta externa (afconvert) mockada."""

import subprocess
from pathlib import Path
from unittest.mock import patch

from services.text_to_speech_service import _convert_to_telegram_friendly_format


def test_converts_to_m4a_on_macos_when_afconvert_available(tmp_path):
    source = tmp_path / "fala.aiff"
    source.write_bytes(b"fake-aiff-bytes")

    def _fake_afconvert(cmd, **kwargs):
        # Simula o afconvert criando o arquivo .m4a de destino.
        target = Path(cmd[-1])
        target.write_bytes(b"fake-m4a-bytes")

    with (
        patch("services.text_to_speech_service.platform.system", return_value="Darwin"),
        patch("services.text_to_speech_service.shutil.which", return_value="/usr/bin/afconvert"),
        patch("services.text_to_speech_service.subprocess.run", side_effect=_fake_afconvert),
    ):
        result = _convert_to_telegram_friendly_format(source)

    assert result.suffix == ".m4a"
    assert result.exists()
    assert not source.exists()  # o .aiff original é removido após a conversão


def test_keeps_original_file_when_afconvert_is_unavailable(tmp_path):
    source = tmp_path / "fala.aiff"
    source.write_bytes(b"fake-aiff-bytes")

    with (
        patch("services.text_to_speech_service.platform.system", return_value="Linux"),
    ):
        result = _convert_to_telegram_friendly_format(source)

    assert result == source
    assert source.exists()


def test_keeps_original_file_when_conversion_fails(tmp_path):
    source = tmp_path / "fala.aiff"
    source.write_bytes(b"fake-aiff-bytes")

    with (
        patch("services.text_to_speech_service.platform.system", return_value="Darwin"),
        patch("services.text_to_speech_service.shutil.which", return_value="/usr/bin/afconvert"),
        patch(
            "services.text_to_speech_service.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "afconvert"),
        ),
    ):
        result = _convert_to_telegram_friendly_format(source)

    assert result == source
    assert source.exists()
