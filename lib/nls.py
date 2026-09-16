import os
import json
import inspect
from logger import logger
from flask import has_request_context, g

#logger = logging.getLogger(__name__)

class SafeDict(dict):
  def __missing__(self, key):
    return f'{{{key}}}'


class NLSManager:
    def __init__(self, base_file: str):
        self._dictionary = {}
        
        # Pfad ermitteln: nls/<module_name>.json
        mod_dir = os.path.dirname(os.path.abspath(base_file))
        mod_name = os.path.splitext(os.path.basename(base_file))[0]
        nls_path = os.path.join(mod_dir, "nls", f"{mod_name}.json")

        if os.path.exists(nls_path):
            try:
                with open(nls_path, "r", encoding="utf-8") as fp:
                    self._dictionary = json.load(fp)
            except Exception as e:
                logger.warning(f"Failed to load NLS file '{nls_path}': {e}")

    def get_current_lang(self) -> str:
        if has_request_context():
            if hasattr(g, "lang") and g.lang:
                return g.lang

        env_lang = os.environ.get("LANG", "").split("_")[0]
        if env_lang:
            return env_lang

        return "en"

    def translate(self, key_or_text: str, lang: str = None) -> str:
        if not lang:
            lang = self.get_current_lang()

        entry = self._dictionary.get(key_or_text)

        if isinstance(entry, dict):
            if lang in entry and entry[lang]:
                return entry[lang]
            if "en" in entry and entry["en"]:
                return entry["en"]
        elif isinstance(entry, str):
            return entry

        return key_or_text

    def __call__(self, key_or_text: str) -> str:
        return self.translate(key_or_text)

    def fmt_locals(self, key_or_text: str) -> str:
        translated_text = self.translate(key_or_text)
   
        caller_frame = inspect.currentframe().f_back
        try:
          caller_locals = caller_frame.f_locals
          return translated_text.format_map(SafeDict(caller_locals))
        finally:
          del caller_frame

    fl=fmt_locals
    f=fmt_locals


