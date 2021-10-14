import json
from time import sleep
from typing import Any, Dict, List, Optional

import httpx
from httpx import HTTPError, Response, TimeoutException
from loguru import logger
from markdownify import markdownify


class Utility:
    """Utilitarian functions designed for Broadcast."""

    def GET(self: Any, url: str, isRetry: bool = False) -> Optional[Dict[str, Any]]:
        """Perform an HTTP GET request and return its response."""

        logger.debug(f"GET {url}")

        try:
            res: Response = httpx.get(url)
            status: int = res.status_code
            data: str = res.text

            res.raise_for_status()
        except HTTPError as e:
            if isRetry is False:
                logger.debug(f"(HTTP {status}) GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"(HTTP {status}) GET {url} failed, {e}")

            return
        except TimeoutException as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            # TimeoutException is common, no need to log as error
            logger.debug(f"GET {url} failed, {e}")

            return
        except Exception as e:
            if isRetry is False:
                logger.debug(f"GET {url} failed, {e}... Retry in 10s")

                sleep(10)

                return Utility.GET(self, url, True)

            logger.error(f"GET {url} failed, {e}")

            return

        logger.trace(data)

        return json.loads(data)

    def POST(self: Any, url: str, payload: Dict[str, Any]) -> bool:
        """Perform an HTTP POST request and return its status."""

        try:
            res: Response = httpx.post(
                url,
                data=json.dumps(payload),
                headers={"content-type": "application/json"},
            )
            status: int = res.status_code
            data: str = res.text

            res.raise_for_status()
        except HTTPError as e:
            logger.error(f"(HTTP {status}) POST {url} failed, {e}")

            return False
        except TimeoutException as e:
            # TimeoutException is common, no need to log as error
            logger.debug(f"POST {url} failed, {e}")

            return False
        except Exception as e:
            logger.error(f"POST {url} failed, {e}")

            return False

        logger.trace(data)

        return True

    def ConvertHTML(self: Any, input: str) -> str:
        """Convert the provided HTML string to markdown format."""

        return markdownify(input, heading_style="ATX", bullets="-")

    def Unslug(self: Any, input: str) -> str:
        """Convert the provided slug strings to a human-readable format."""

        alwaysCaps: List[str] = ["COD", "CDL"]

        result: str = ""

        items: List[str] = input.split(",")
        i: int = 0

        for item in items:
            parts: List[str] = item.split("-")
            p: int = 0

            for part in parts:
                if (v := part.upper()) in alwaysCaps:
                    result += v
                else:
                    result += part.title()

                p += 1

                if p < len(parts):
                    result += " "
            i += 1

            if i < len(items):
                result += ", "

        return result
