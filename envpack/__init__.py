"""envpack — snapshot, encrypt, and sync .env files across machines."""

__version__ = "0.1.0"
__author__ = "envpack contributors"


def get_version() -> str:
    """Return the current version string of envpack.

    Returns
    -------
    str
        The version string in PEP 440 format (e.g. ``"0.1.0"``).

    Examples
    --------
    >>> import envpack
    >>> envpack.get_version()
    '0.1.0'
    """
    return __version__
