# File: lib/kernel/config.py

from configparser import ConfigParser
import urllib.request
import urllib.error
import time
import sys
import secrets
from pathlib import Path
from logger import *
from pprint import pprint


class AutoReloadConfigParser(dict):
    def __init__(self,config_name="config", ttl_seconds=1200):
        super().__init__()

        self.config_file = "/etc/c4dos/%s.ini" % config_name
        self.ttl_seconds = ttl_seconds
        self.last_loaded = 0
        self._parser = ConfigParser()

    def _parse_quoted_value(self, raw_val: str, key: str, section: str) -> str:
            val = raw_val.strip()
            
            if ((val.startswith('"') and val.endswith('"')) \
                 or (val.startswith("'") and val.endswith("'"))):
                content = val[1:-1]
                
                lines = [line.strip() for line in content.splitlines()]
                return "\n".join(lines)
            else:
                raise ValueError(
                    f"Config-ERROR in [{section}] '{key}': " \
                     "quotes missing (Aktuell: {raw_val!r})"
                )


    def read_with_includes(self):
        temp_parser = ConfigParser()
        temp_parser.optionxform = str
        try:
            read_files = temp_parser.read(self.config_file, encoding="utf-8")
            if not read_files:
                raise FileNotFoundError(f"Config file '{self.config_file}' " \
                                         "not found")

            if temp_parser.has_section("include"):
                urls_raw = temp_parser.get("include", "urls", fallback="")
                urls = [u.strip() for u in urls_raw.splitlines() if u.strip()]
                temp_parser.remove_section("include")

                for url in urls:
                    self._load_from_url(temp_parser, url)

            self._parser = temp_parser
            self.clear()
            global_defaults = {}
            if temp_parser.has_section("*"):
               for key, val in temp_parser["*"].items():
                 if isinstance(val, str):
                   #global_defaults[key] = val.strip().strip('"\'')
                   global_defaults[key] = self._parse_quoted_value(val,key,"*")
                 else:
                   global_defaults[key] = val

            for section in temp_parser.sections():
                section_data = global_defaults.copy()
                for key, val in temp_parser[section].items():
                    if isinstance(val, str):
                        #cleanval = val.strip().strip('"\'')
                        cleanval = self._parse_quoted_value(val,key,section)
                    else:
                        cleanval = val
                    section_data[key] = cleanval

                self[section] = section_data


            self.last_loaded = time.time()

            if ("GLOBAL" not in self):
              self["GLOBAL"] = global_defaults.copy()

            if (not self["GLOBAL"].get("X-AUTHKEY")):
              self["GLOBAL"]["X-AUTHKEY"] = secrets.token_hex(64)
              logger.info("dynamic generated X-AUTHKEY for [GLOBAL] section!")

            if (not self["GLOBAL"].get("BASE_DIR")):
              self["GLOBAL"]["BASE_DIR"]= \
                  str(Path(__file__).resolve().parents[1])

            logger.debug(f"Config '{self.config_file}' successfuly loaded")

        except Exception as e:
            logger.warning(f"Config load failed: {e}. " \
                            "using old.")
            if self.last_loaded == 0:
                raise e

    def _load_from_url(self, target_parser, url: str):
        req = urllib.request.Request(url, headers={
              'User-Agent': 'Python-ConfigParser'})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode("utf-8")
            target_parser.read_string(content, source=url)

    def _check_ttl(self):
       if time.time() - self.last_loaded > self.ttl_seconds:
           self.read_with_includes()

    def get(self, section, option, fallback=None):
       self._check_ttl()
       return self._parser.get(section, option, fallback=fallback)

    def getint(self, section, option, fallback=None):
       self._check_ttl()
       return self._parser.getint(section, option, fallback=fallback)

    def getboolean(self, section, option, fallback=None):
       self._check_ttl()
       return self._parser.getboolean(section, option, fallback=fallback)

    def __getitem__(self, key):
        self._check_ttl()
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._check_ttl()
        return super().get(key, default)

    def __iter__(self):
        self._check_ttl()
        return super().__iter__()

    def items(self):
        self._check_ttl()
        return super().items()

    def values(self):
        self._check_ttl()
        return super().values()




# Singleton-Instanz erzeugen
main_mod = sys.modules["__main__"]
config_name = getattr(main_mod, "__CONFIG__", "noDEFAULT")

config = AutoReloadConfigParser(config_name=config_name, ttl_seconds=30)
config.read_with_includes()


