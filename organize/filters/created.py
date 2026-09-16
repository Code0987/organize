import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Optional, Union

from organize.filter import FilterConfig

from .common.timefilter import TimeFilter


def _valid_timestamp(value: Union[int, float, str, None]) -> Optional[float]:
    """Return a usable POSIX timestamp, or None if birth time is unknown.

    GNU coreutils `stat --format=%W` returns 0 when the filesystem does not
    expose a birth time (common on WSL/drvfs, network mounts, and some tmpfs).
    Treating that 0 as a real timestamp produced 1970-01-01.
    """
    if value is None:
        return None
    try:
        timestamp = float(value)
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return timestamp


def read_stat_created(path: Path) -> Optional[float]:
    if sys.platform == "win32":
        return None
    if sys.platform == "darwin" or sys.platform.startswith("freebsd"):
        cmd = ["stat", "-f", "%B", str(path)]
    else:
        cmd = ["stat", "--format=%W", str(path)]
    try:
        created_str = subprocess.check_output(
            cmd,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None
    return _valid_timestamp(created_str)


def read_created(path: Path) -> datetime:
    timestamp = None
    stat_result = path.stat()

    # ctime is the creation time only in Windows.
    # On unix it's the datetime of the last metadata change.
    if sys.platform == "win32":
        timestamp = _valid_timestamp(stat_result.st_ctime)
    else:
        # On other Unix systems (such as FreeBSD), the following
        # attributes may be available (but may be only filled out if
        # root tries to use them):
        try:
            timestamp = _valid_timestamp(stat_result.st_birthtime)  # type: ignore
        except AttributeError:
            pass

    # If we still haven't gotten a timestamp, we try the (slower) fallback
    # method using the `stat` tool.
    if timestamp is None:
        timestamp = read_stat_created(path)

    # Last resort: ctime. On Unix this is last metadata change, not birth
    # time, but it is the closest portable value and avoids treating an
    # unknown birth time as 1970-01-01.
    if timestamp is None:
        timestamp = _valid_timestamp(stat_result.st_ctime)

    # give up.
    if timestamp is None:
        raise EnvironmentError("The creation time is not available.")

    return datetime.fromtimestamp(timestamp, timezone.utc)


class Created(TimeFilter):
    """Matches files / folders by created date

    Attributes:
        years (int): specify number of years
        months (int): specify number of months
        weeks (float): specify number of weeks
        days (float): specify number of days
        hours (float): specify number of hours
        minutes (float): specify number of minutes
        seconds (float): specify number of seconds
        mode (str):
            either 'older' or 'newer'. 'older' matches files / folders created before
            the given time, 'newer' matches files / folders created within the given
            time. (default = 'older')

    Returns:
        `{created}` (datetime): The datetime the file / folder was created.
    """

    filter_config: ClassVar[FilterConfig] = FilterConfig(
        name="created",
        files=True,
        dirs=True,
    )

    def get_datetime(self, path: Path) -> datetime:
        return read_created(path)
