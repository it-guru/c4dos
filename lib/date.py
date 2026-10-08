import re
import sys
from datetime import datetime, timezone
from typing import Optional, Union, Tuple, Dict, Any


try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        from dateutil.tz import gettz as ZoneInfo


from nls import NLSManager
_ = NLSManager(__file__)



def expand_time_expression(val: str,
                            output_format: str = "en",
                            src_tz: Union[str, ZoneInfo] = "UTC",
                            dst_tz: Union[str, ZoneInfo] = "UTC",
                            def_hour: int = 0,
                            def_min: int = 0,
                            def_sec: int = 0,
                            i18n_labels: Optional[Dict[str, str]] = None,
                            return_tuple: bool = False
                        )->Union[str,Tuple[int,int,int,int,int,int],None]:
    """
    Expands relative or absolute time expressions into a formatted 
    string or datetime tuple.

    Supported base expressions:
      - 'now' (or i18n variant)
      - 'today' (or i18n variant, resets time to def_hour/def_min/def_sec)
      - 'monthbase' (or i18n variant, resets to 1st of month with default time)
      - Absolute formats: 
           YYYYMMDDHHMMSSZ, 
           YYYYMMDDHHMMSS, 
           MM/YY, 
           YYYY-MM-DD HH:MM:SS,
           ISO8601 (T-notation),
           DD.MM.YYYY HH:MM[:SS], 
           DD.MM.YYYY,
           DD.MM., 
           YYYY-MM-DD, 
           HH:MM[:SS]

    Supported relative modifiers (chained):
      - +1h / -2h (hours)
      - +1M / -2M (months)
      - +1Y / -2Y (years)
      - +1m / -2m (minutes)
      - +1w / -2w (weeks)
      - +1d / -2d (days)
      - +1s / -2s (seconds)
    """
    if not val:
        return None

    org_val = val.strip()
    val_str = org_val

    # Resolve timezones
    src_tz_obj = ZoneInfo(src_tz) if isinstance(src_tz, str) else src_tz
    dst_tz_obj = ZoneInfo(dst_tz) if isinstance(dst_tz, str) else dst_tz

    # Build translation keywords
    now_labels = {"now"}
    today_labels = {"today"}
    monthbase_labels = {"monthbase"}

    if i18n_labels:
        if "now" in i18n_labels:
            now_labels.add(i18n_labels["now"].lower())
        if "today" in i18n_labels:
            today_labels.add(i18n_labels["today"].lower())
        if "monthbase" in i18n_labels:
            monthbase_labels.add(i18n_labels["monthbase"].lower())

    dt: Optional[datetime] = None

    # Helper to create localized datetime in src_tz and convert to dst_tz
    def make_dt(year: int, month: int, day: int, hour: int, minute: int, second: int, tz_override=None) -> datetime:
        tz = tz_override or src_tz_obj
        local_dt = datetime(year, month, day, hour, minute, second, tzinfo=tz)
        return local_dt.astimezone(dst_tz_obj)

    # -------------------------------------------------------------------------
    # 1. Base anchor matching
    # -------------------------------------------------------------------------
    val_lower = val_str.lower()
    matched_label = None

    for label in now_labels:
        if val_lower.startswith(label):
            matched_label = label
            dt = datetime.now(tz=dst_tz_obj)
            val_str = val_str[len(matched_label):]
            break

    if dt is None:
        for label in today_labels:
            if val_lower.startswith(label):
                matched_label = label
                now_src = datetime.now(tz=src_tz_obj)
                dt = make_dt(now_src.year, now_src.month, now_src.day, def_hour, def_min, def_sec)
                val_str = val_str[len(matched_label):]
                break

    if dt is None:
        for label in monthbase_labels:
            if val_lower.startswith(label):
                matched_label = label
                now_src = datetime.now(tz=src_tz_obj)
                dt = make_dt(now_src.year, now_src.month, 1, def_hour, def_min, def_sec)
                val_str = val_str[len(matched_label):]
                break

    # Absolute formats if no keyword matched
    if dt is None:
        # YYYYMMDDHHMMSSZ (LDAP GMT format)
        m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z", val_str)
        if m:
            y, mth, d, h, mn, s = map(int, m.groups())
            dt = make_dt(y, mth, d, h, mn, s, tz_override=timezone.utc)
            val_str = val_str[m.end():]

    if dt is None:
        # YYYYMMDDHHMMSS
        m = re.match(r"^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", val_str)
        if m:
            y, mth, d, h, mn, s = map(int, m.groups())
            dt = make_dt(y, mth, d, h, mn, s)
            val_str = val_str[m.end():]

    if dt is None:
        # MM/YY
        m = re.match(r"^(\d+)/(\d+)", val_str)
        if m:
            mth, y = map(int, m.groups())
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, 1, def_hour, def_min, def_sec)
            val_str = val_str[m.end():]

    if dt is None:
        # YYYY-MM-DD HH:MM:SS [TZ]
        m = re.match(r"^(\d+)-(\d+)-(\d+)\s+(\d+):(\d+):(\d+)(?:\s+([A-Za-z]+))?", val_str)
        if m:
            y, mth, d, h, mn, s = map(int, m.groups()[:6])
            tz_str = m.group(7)
            override_tz = ZoneInfo(tz_str) if tz_str else None
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, d, h, mn, s, tz_override=override_tz)
            val_str = val_str[m.end():]

    if dt is None:
        # YYYY-MM-DDTHH:MM:SS[.frac][Z]
        m = re.match(r"^(\d{4})-(\d+)-(\d+)T(\d+):(\d+):(\d+)(?:\.\d*)?(Z)?", val_str)
        if m:
            y, mth, d, h, mn, s = map(int, m.groups()[:6])
            is_utc = m.group(7) == "Z"
            override_tz = timezone.utc if is_utc else src_tz_obj
            dt = make_dt(y, mth, d, h, mn, s, tz_override=override_tz)
            val_str = val_str[m.end():]

    if dt is None:
        # DD.MM.YYYY HH:MM:SS [TZ]
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)\s+(\d+):(\d+):(\d+)(?:\s+([A-Za-z]+))?", val_str)
        if m:
            d, mth, y, h, mn, s = map(int, m.groups()[:6])
            tz_str = m.group(7)
            override_tz = ZoneInfo(tz_str) if tz_str else None
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, d, h, mn, s, tz_override=override_tz)
            val_str = val_str[m.end():]

    if dt is None:
        # DD.MM.YYYY HH:MM
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)\s+(\d+):(\d+)", val_str)
        if m:
            d, mth, y, h, mn = map(int, m.groups())
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, d, h, mn, 0)
            val_str = val_str[m.end():]

    if dt is None:
        # DD.MM.YYYY
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)", val_str)
        if m:
            d, mth, y = map(int, m.groups())
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, d, def_hour, def_min, def_sec)
            val_str = val_str[m.end():]

    if dt is None:
        # DD.MM. (Current year)
        m = re.match(r"^(\d+)\.(\d+)\.", val_str)
        if m:
            d, mth = map(int, m.groups())
            now_src = datetime.now(tz=src_tz_obj)
            dt = make_dt(now_src.year, mth, d, def_hour, def_min, def_sec)
            val_str = val_str[m.end():]

    if dt is None:
        # YYYY-MM-DD
        m = re.match(r"^(\d+)-(\d+)-(\d+)", val_str)
        if m:
            y, mth, d = map(int, m.groups())
            if y < 50:
                y += 2000
            elif y <= 99:
                y += 1900
            dt = make_dt(y, mth, d, def_hour, def_min, def_sec)
            val_str = val_str[m.end():]

    if dt is None:
        # HH:MM:SS (Today in src_tz)
        m = re.match(r"^(\d+):(\d+):(\d+)", val_str)
        if m:
            h, mn, s = map(int, m.groups())
            now_src = datetime.now(tz=src_tz_obj)
            dt = make_dt(now_src.year, now_src.month, now_src.day, h, mn, s)
            val_str = val_str[m.end():]

    if dt is None:
        # HH:MM (Today in src_tz)
        m = re.match(r"^(\d+):(\d+)", val_str)
        if m:
            h, mn = map(int, m.groups())
            now_src = datetime.now(tz=src_tz_obj)
            dt = make_dt(now_src.year, now_src.month, now_src.day, h, mn, 0)
            val_str = val_str[m.end():]

    if dt is None:
        return None

    # -------------------------------------------------------------------------
    # 2. Process relative modifiers (chaining)
    # -------------------------------------------------------------------------
    modifier_pattern = re.compile(r"^([\+-]\d+)([hMYmwds])")

    while val_str:
        val_str = val_str.lstrip()
        if not val_str:
            break

        m = modifier_pattern.match(val_str)
        if not m:
            # Unparseable remaining characters
            return None

        amount = int(m.group(1))
        unit = m.group(2)
        val_str = val_str[m.end():]

        if unit == "h":
            dt += timedelta(hours=amount)
        elif unit == "m":
            dt += timedelta(minutes=amount)
        elif unit == "s":
            dt += timedelta(seconds=amount)
        elif unit == "d":
            dt += timedelta(days=amount)
        elif unit == "w":
            dt += timedelta(weeks=amount)
        elif unit == "M":
            dt = add_months(dt, amount)
        elif unit == "Y":
            dt = add_years(dt, amount)

    # -------------------------------------------------------------------------
    # 3. Output generation
    # -------------------------------------------------------------------------
    #if return_tuple:
    t_tuble=(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    return date_to_string(dt, output_format, dst_tz=dst_tz_obj),t_tuble


def add_months(dt: datetime, months: int) -> datetime:
    """Helper to add/subtract months without external heavy dependencies."""
    new_month = dt.month - 1 + months
    new_year = dt.year + new_month // 12
    new_month = new_month % 12 + 1
    # Adjust day if target month has fewer days
    max_days = [31, 29 if (new_year % 4 == 0 and (new_year % 100 != 0 or new_year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][new_month - 1]
    new_day = min(dt.day, max_days)
    return dt.replace(year=new_year, month=new_month, day=new_day)


def add_years(dt: datetime, years: int) -> datetime:
    """Helper to add/subtract years."""
    new_year = dt.year + years
    # Handle leap year edge case (Feb 29 -> Feb 28)
    if dt.month == 2 and dt.day == 29 and not (new_year % 4 == 0 and (new_year % 100 != 0 or new_year % 400 == 0)):
        return dt.replace(year=new_year, month=2, day=28)
    return dt.replace(year=new_year)


from datetime import timedelta


def date_to_string(dt: datetime, output_format: str = "en", dst_tz: Optional[Union[str, ZoneInfo]] = None) -> str:
    """Formats a datetime object according to the requested target format."""
    if dst_tz:
        tz_obj = ZoneInfo(dst_tz) if isinstance(dst_tz, str) else dst_tz
        if dt.tzinfo != tz_obj:
            dt = dt.astimezone(tz_obj)

    fmt = output_format.lower() if output_format else "en"

    if fmt == "de":
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    elif fmt == "datetime":
        return dt
    elif fmt == "unixtime":
        return str(int(dt.timestamp()))
    elif fmt == "iso8601":
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif fmt == "rfc822":
        return dt.strftime("%a, %d %b %Y %H:%M:%S %z")
    elif fmt in ("soap", "iso"):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    elif fmt == "edm":
        return dt.strftime("%Y-%m-%dT%H:%M:%S")
    elif fmt == "ics":
        return dt.strftime("%Y%m%dT%H%M%SZ")
    elif fmt == "ultrashort":
        now = datetime.now(tz=dt.tzinfo)
        if (dt.year, dt.month, dt.day) == (now.year, now.month, now.day):
            return dt.strftime("%H:%M")
        return dt.strftime("%d.%m.%y")
    elif fmt == "deday":
        return dt.strftime("%d.%m.%y")
    elif fmt == "enday":
        return dt.strftime("%Y-%m-%d")
    elif fmt != "stamp" and output_format is not None:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Default 'stamp' format
        return dt.strftime("%Y%m%d%H%M%S")


