from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, time as dtime
from glob import glob
import http.client
import json
import logging
import os
from pathlib import Path
import socket
import threading
import time
from typing import Dict, List, Set
import urllib.error
import urllib.request
from config import config
from pprint import pprint
from logger import logger


class DynamicScheduler(threading.Thread):

  def __init__(self):
    super().__init__(daemon=True)
    self.config_patterns = []
    self.auth_key = config["GLOBAL"]["X-AUTHKEY"]
    self.http_agent = urllib.request

    self._file_mtimes = {}  # type: Dict[str, float]
    self._jobs = []  # type: List[dict]
    self._executor = ThreadPoolExecutor(
        max_workers=5, thread_name_prefix="CronJob"
    )
    self._running = True

  @staticmethod
  def _calculate_next_run(job: dict, now_dt: datetime) -> float:
    if ("interval" in job \
        and job["interval"] is not None \
        and job["interval"] > 0):
      return (now_dt + timedelta(seconds=int(job["interval"]))).timestamp()

    time_str = job.get("time")
    if not time_str or ":" not in time_str:
      return (now_dt + timedelta(minutes=1)).timestamp()

    hour, minute = map(int, time_str.split(":"))

    weekday_map = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }
    allowed_weekdays = None
    if "weekdays" in job and job["weekdays"]:
      allowed_weekdays = set()
      for w in job["weekdays"]:
        if isinstance(w, int):
          allowed_weekdays.add(w % 7)
        elif isinstance(w, str):
          w_clean = w.lower()[:3]
          if w_clean in weekday_map:
            allowed_weekdays.add(weekday_map[w_clean])

    allowed_month_days = None
    if "month_days" in job and job["month_days"]:
      allowed_month_days = set(job["month_days"])

    candidate_date = now_dt.date()

    for _ in range(366):
      candidate_dt = datetime.combine(candidate_date, dtime(hour, minute))

      if candidate_dt > now_dt + timedelta(seconds=1):
        if (
            allowed_weekdays is not None
            and candidate_dt.weekday() not in allowed_weekdays
        ):
          candidate_date += timedelta(days=1)
          continue

        if (
            allowed_month_days is not None
            and candidate_dt.day not in allowed_month_days
        ):
          candidate_date += timedelta(days=1)
          continue

        return candidate_dt.timestamp()

      candidate_date += timedelta(days=1)

    return (now_dt + timedelta(days=1)).timestamp()

  def _resolve_all_file_paths(self) -> Set[Path]:
    base_dir=Path(config["GLOBAL"]["BASE_DIR"])
    self.config_patterns = [
        str(base_dir / "crontab.json"),  # Global crontab in root
        str(base_dir / "config" / "crons"),  # Directory with multiple .jsons
        str(base_dir / "mod" / "*" / "crontab.json"),  # Wildcard across modules
    ]

    modpath_str = config.get("GLOBAL", {}).get("MOD_PATH", "")
    raw_paths = [p.strip() for p in modpath_str.split(":") if p.strip()]
    for raw_path in raw_paths:
       if not raw_path.startswith("/"):
          dir_path = Path(base_dir) / raw_path
       else:
          dir_path = Path(raw_path)
       self.config_patterns.append(dir_path / "crontab.json")
       self.config_patterns.append(dir_path / "mod" / "*" / "crontab.json")

    found_files = set()  # type: Set[Path]

    for pattern in self.config_patterns:
      logger.debug("scheduler: loading pattern: '%s'" % str(pattern))
      matches = glob(str(pattern), recursive=True)

      for match_str in matches:
        p = Path(match_str).resolve()
        if p.is_file() and p.name.endswith(".json"):
          found_files.add(p)
        elif p.is_dir():
          for json_file in p.rglob("crontab.json"):
            if json_file.is_file():
              found_files.add(json_file.resolve())

    for json_file in found_files:
       logger.debug("scheduler: using cron file: '%s'" % str(json_file))

    return found_files


  def _load_config(self):
    try:
      current_files = self._resolve_all_file_paths()
      current_mtimes = {}
      logger.debug("start scheduler._load_config")

      for file_path in current_files:
        try:
          current_mtimes[str(file_path)] = file_path.stat().st_mtime
        except OSError:
          continue

      if current_mtimes == self._file_mtimes:
        return

      now_dt = datetime.now()
      new_jobs = []

      for file_str in current_mtimes.keys():
        file_path = Path(file_str)
        try:
          with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

          if not isinstance(raw_data, list):
            logger.warning(
                f"File {file_path.name} does not contain a JSON list. Skipping."
            )
            continue

          for item in raw_data:
            if not item.get("enabled", True):
              continue

            job = {
                "name": item.get("name", "Unnamed Job"),
                "source_file": file_path.name,
                "interval": item.get("interval"),
                "time": item.get("time"),
                "weekdays": item.get("weekdays"),
                "month_days": item.get("month_days"),
                "ports": item.get("ports", [8081]),
                "endpoint": item.get("endpoint", "/"),
                "method": item.get("method", "GET").upper(),
            }

            job["next_run"] = self._calculate_next_run(job, now_dt)
            new_jobs.append(job)

        except json.JSONDecodeError:
          logger.error(
              f"Failed to parse JSON in {file_path}. Keeping previous schedule"
              " for this file."
          )
        except Exception as e:
          logger.error(f"Unexpected error reading {file_path}: {e}")
      self._jobs = new_jobs
      self._file_mtimes = current_mtimes
      logger.info(
          f"Reloaded cron schedules across {len(current_mtimes)} file(s)."
          f" Total active jobs: {len(self._jobs)}"
      )

    except Exception as e:
      logger.error(f"Error during cron configuration scan: {e}")


  def _execute_request(
          self,
          target_port: int,
          endpoint: str,
          method: str,
          job_name: str,
          source_file: str,
      ):
        target = f"http://127.0.0.1:{target_port}"
        url = f"{target}{endpoint}"

        try:
          req = urllib.request.Request(url, method=method)
          req.add_header("X-AUTHKEY", self.auth_key)
          req.add_header("User-Agent", "c4dos-CronScheduler/1.0")

          no_proxy_handler = urllib.request.ProxyHandler({})
          opener = urllib.request.build_opener(no_proxy_handler)

          with opener.open(req, timeout=5) as response:
            result = response.read().decode("utf-8")
            logger.debug(f"[{job_name} ({source_file})]:")
            logger.debug(f" {method} {url} ->")
            logger.debug(f" result: {response.status}")

        except urllib.error.HTTPError as e:
          logger.warning(f"[{job_name} ({source_file})] HTTP {e.code} "\
                          "({e.reason}) for {url}"
          )
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            socket.error,
            ConnectionResetError,
        ) as e:
          logger.warning(
              f"[{job_name} ({source_file})] Network error for {url}: {e}"
          )
        except Exception as e:
          logger.error(
              f"[{job_name} ({source_file})] Unexpected error for {url}: {e}"
          )


  def run(self):
    time.sleep(3.0)
    logger.info("CronScheduler background thread started.")
    loopCount=0
    while self._running:
      if (loopCount>59):
         loopCount=0
      if (loopCount==0): 
         self._load_config()
      loopCount+=1

      now_dt = datetime.now()
      now_ts = now_dt.timestamp()

      for job in self._jobs:
        if now_ts >= job["next_run"]:
          job["next_run"] = self._calculate_next_run(job, now_dt)

          for port in job["ports"]:
            self._executor.submit(
                self._execute_request,
                port,
                job["endpoint"],
                job["method"],
                job["name"],
                job.get("source_file", "unknown"),
            )

      time.sleep(1.0)

  def stop(self):
    """Gracefully shuts down scheduler thread."""
    self._running = False
    self._executor.shutdown(wait=False)

