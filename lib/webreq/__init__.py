from .base import WebReq

from .BasicAuth   import WebReqBasicAuth
from .Tardis      import WebReqTardis

__all__ = [k for k in locals() if k.startswith("WebReq")]



