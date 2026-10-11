""" Unit tests for utility functions. """

import typer


def test_open_file_in_default_viewer_invalid_path(mocker):
    """Test that an invalid file path raises a typer.Exit."""
    mocker.patch("pathlib.Path.is_file", return_value=False)
    mocker.patch("rich.console.Console.print")

    from src.utils import open_file_in_default_viewer

    try:
        open_file_in_default_viewer("invalid_path.pdf")
    except typer.Exit as e:
        assert e.exit_code == 1


def test_open_file_in_default_viewer_valid_path(mocker):
    """Test that a valid file path attempts to open the file."""
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mock_subprocess = mocker.patch("subprocess.run")
    mocker.patch("rich.console.Console.print")

    from src.utils import open_file_in_default_viewer

    open_file_in_default_viewer("valid_path.pdf")

    # Check that subprocess.run was called (the exact command depends on the OS)
    assert mock_subprocess.called


def test_open_file_in_default_viewer_exception(mocker):
    """Test that an exception during file opening raises a RuntimeError."""
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("subprocess.run", side_effect=Exception("Mocked exception"))
    mocker.patch("rich.console.Console.print")

    from src.utils import open_file_in_default_viewer

    try:
        open_file_in_default_viewer("valid_path.pdf")
    except RuntimeError as e:
        assert "Failed to open file" in str(e)


def test_open_file_in_default_viewer_success(mocker):
    """Test that a valid file path successfully opens the file."""
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mock_subprocess = mocker.patch("subprocess.run")
    mocker.patch("rich.console.Console.print")

    from src.utils import open_file_in_default_viewer

    open_file_in_default_viewer("valid_path.pdf")

    # Check that subprocess.run was called (the exact command depends on the OS)
    assert mock_subprocess.called


def test_open_file_in_default_viewer_empty_path(mocker):
    """Test that an empty file path raises a typer.Exit."""
    mocker.patch("pathlib.Path.is_file", return_value=False)
    mocker.patch("rich.console.Console.print")

    from src.utils import open_file_in_default_viewer

    try:
        open_file_in_default_viewer("")
    except typer.Exit as e:
        assert e.exit_code == 1
