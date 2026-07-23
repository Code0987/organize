import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import ClassVar, Optional

from organize.filter import FilterConfig

from .common.timefilter import TimeFilter


def _valid_timestamp(value: Optional[float]) -> Optional[float]:
    """Return *value* only if it looks like a real creation timestamp.

    GNU ``stat --format=%W`` returns ``0`` when the birth time is unknown.
    Some platforms expose ``st_birthtime == 0`` in the same situation. Treat
    those as "unavailable" so callers do not see 1970-01-01 as a real date.
    """
    if value is None:
        return None
    if value <= 0:
        return None
    return value


def read_stat_created(path: Path) -> Optional[int]:
    commands = (
        ["stat", "--format=%W", str(path)],  # GNU coreutils
        ["stat", "-f %B", str(path)],  # BSD
    )
    for cmd in commands:
        try:
            created_str = subprocess.check_output(cmd, encoding="utf-8").strip()
            timestamp = int(created_str)
            valid = _valid_timestamp(timestamp)
            if valid is not None:
                return int(valid)
        except (subprocess.CalledProcessError, ValueError):
            pass
    return None


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
