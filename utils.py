import json
import re
from time import sleep
from typing import Any, Dict, List, Optional

import httpx
from httpx import HTTPError, Response, TimeoutException
from loguru import logger


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

    def StripHTML(self: Any, input: str) -> str:
        """Remove the HTML formatting from the provided string."""

        expression: re.Pattern[str] = re.compile(
            "<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});"
        )

        return re.sub(expression, "", input)

    def Unslug(self: Any, input: str) -> str:
        """Convert the provided slug strings to a human-readable format."""

        result: str = ""

        items: List[str] = input.split(",")
        i: int = 0

        for item in items:
            parts: List[str] = item.split("-")
            p: int = 0

            for part in parts:
                result += part.title()

                p += 1

                if p < len(parts):
                    result += " "
            i += 1

            if i < len(items):
                result += ", "

        return result
