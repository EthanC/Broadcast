import json
from datetime import datetime
from sys import exit, stderr
from typing import Any, Dict, List, Optional, Union

from loguru import logger
from notifiers.logging import NotificationHandler

from utils import Utility


class Broadcast:
    """
    Call of Duty feed watcher that reports the news via Discord.

    https://github.com/EthanC/Broadcast
    """

    def Initialize(self: Any) -> None:
        """Initialize Broadcast and begin primary functionality."""

        logger.info("Broadcast")
        logger.info("https://github.com/EthanC/Broadcast")

        self.config: Dict[str, Any] = Broadcast.LoadConfig(self)

        Broadcast.SetupLogging(self)

        self.changed: bool = False
        self.history: Dict[str, Any] = Broadcast.LoadHistory(self)

        sources: Dict[str, Dict[str, Any]] = self.config["sources"]

        if sources["blog"]["enable"] is True:
            Broadcast.ProcessBlog(self, sources["blog"]["language"])

        if sources["motd"]["enable"] is True:
            Broadcast.ProcessMOTD(self, sources["motd"]["language"])

        if self.changed is True:
            Broadcast.SaveHistory(self)

        logger.success("Finished processing feeds")

    def LoadConfig(self: Any) -> Dict[str, Any]:
        """Load the configuration values specified in config.json"""

        try:
            with open("config.json", "r") as file:
                config: Dict[str, Any] = json.loads(file.read())
        except Exception as e:
            logger.critical(f"Failed to load configuration, {e}")

            exit(1)

        logger.success("Loaded configuration")

        return config

    def SetupLogging(self: Any) -> None:
        """Setup the logger using the configured values."""

        settings: Dict[str, Any] = self.config["logging"]

        if (level := settings["severity"].upper()) != "DEBUG":
            try:
                logger.remove()
                logger.add(stderr, level=level)

                logger.success(f"Set logger severity to {level}")
            except Exception as e:
                # Fallback to default logger settings
                logger.add(stderr, level="DEBUG")

                logger.error(f"Failed to set logger severity to {level}, {e}")

        if settings["discord"]["enable"] is True:
            level: str = settings["discord"]["severity"].upper()
            url: str = settings["discord"]["webhookUrl"]

            try:
                # Notifiers library does not natively support Discord at
                # this time. However, Discord will accept payloads which
                # are compatible with Slack by appending to the url.
                # https://github.com/liiight/notifiers/issues/400
                handler: NotificationHandler = NotificationHandler(
                    "slack", defaults={"webhook_url": f"{url}/slack"}
                )

                logger.add(
                    handler,
                    level=level,
                    format="```\n{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} - {message}\n```",
                )

                logger.success(f"Enabled logging to Discord with severity {level}")
            except Exception as e:
                logger.error(f"Failed to enable logging to Discord, {e}")

    def LoadHistory(self: Any) -> Dict[str, Any]:
        """Load the last seen feed items specified in history.json"""

        try:
            with open("history.json", "r") as file:
                history: Dict[str, Any] = json.loads(file.read())
        except FileNotFoundError:
            history: Dict[str, Any] = {"blog": [], "motd": []}
            self.changed = True

            logger.success("Feed history not found, created empty file")
        except Exception as e:
            logger.critical(f"Failed to load feed history, {e}")

            exit(1)

        if history.get("blog") is None:
            history["blog"] = []

        if history.get("motd") is None:
            history["motd"] = []

        logger.success("Loaded feed history")

        return history

    def ProcessBlog(self: Any, language: str) -> None:
        """
        Get the current Call of Duty blog feed and determine whether or not
        it has updated.
        """

        past: List[str] = self.history["blog"]
        blogChanged: bool = False

        data: Optional[Dict[str, Any]] = Utility.GET(
            self, f"https://www.callofduty.com/site/cod/franchiseFeed/{language}"
        )
        length: int = len(data.get("blog", []))

        try:
            if (data is None) or (length == 0):
                raise ValueError("did not receive a valid response")
            elif length != 105:
                raise ValueError(
                    f"received invalid response (expected length 105 got {length:,})"
                )
        except Exception as e:
            logger.debug(f"Failed to process Call of Duty blog, {e}")

            return

        current: List[str] = []
        data = data["blog"][:5]

        for item in data:
            current.append(item.get("url", "Unknown").replace("?app=true", ""))

        if len(past) == 0:
            logger.info(
                "Call of Duty blog previously untracked, latest feed will be saved to history"
            )

            self.history["blog"] = current
            self.changed = True
            blogChanged = True

            return

        for item in data:
            url: str = item.get("url", "Unknown").replace("?app=true", "")

            if url in past:
                continue

            logger.success(f"New Call of Duty blog post, {url}")

            fields: List[Dict[str, Union[str, bool]]] = []

            if (value := item["metadata"].get("contentItemType")) is not None:
                fields.append(
                    {
                        "name": "Content Type",
                        "value": Utility.Unslug(self, value),
                        "inline": True,
                    }
                )

            if (value := item["metadata"].get("game")) is not None:
                fields.append(
                    {
                        "name": "Game",
                        "value": Utility.Unslug(self, value),
                        "inline": True,
                    }
                )

            success: bool = Broadcast.Notify(
                self,
                {
                    "title": item["title"],
                    "description": item.get("subTitle"),
                    "url": url,
                    "color": int("FFFFFF", base=16),
                    "image": item["dimg"],
                    "author": item.get("author"),
                    "fields": fields,
                },
            )

            # Ensure no changes go without notification
            if success is True:
                self.history["blog"] = current
                self.changed = True
                blogChanged = True

        if blogChanged is not True:
            logger.info("Call of Duty blog not updated")

    def ProcessMOTD(self: Any, language: str) -> None:
        """
        Get the current Call of Duty Message of the Day feed and determine whether
        or not it has updated.
        """

        past: List[str] = self.history["motd"]
        motdChanged: bool = False

        data: Optional[Dict[str, Any]] = Utility.GET(
            self, f"https://www.callofduty.com/site/cod/franchiseFeed/{language}"
        )

        if (data is None) or (len(data.get("mobileMotd", [])) == 0):
            return

        current: List[str] = []
        data = data["mobileMotd"]

        for item in data:
            current.append(item["name"])

        if len(past) == 0:
            logger.info(
                "Call of Duty Message of the Day previously untracked, latest feed will be saved to history"
            )

            self.history["motd"] = current
            self.changed = True
            motdChanged = True

            return

        for item in data:
            name: str = item["name"]

            if name in past:
                continue

            logger.success(f"New Call of Duty Message of the Day, {name}")

            fields: List[Dict[str, Union[str, bool]]] = []

            if (value := item["metadata"].get("priority")) is not None:
                fields.append(
                    {
                        "name": "Priority",
                        "value": f"{value}",
                        "inline": True,
                    }
                )

            self.history["motd"] = current
            self.changed = True
            motdChanged = True

            success: bool = Broadcast.Notify(
                self,
                {
                    "title": item["data"]["title"],
                    "description": Utility.StripHTML(self, item["data"]["entryText"]),
                    "color": int("FFFFFF", base=16),
                    "image": None
                    if (i := item["data"].get("image")) is None
                    else f"https://callofduty.com{i}",
                    "fields": fields,
                },
            )

            # Ensure no changes go without notification
            if success is True:
                self.history["motd"] = current
                self.changed = True
                motdChanged = True

        if motdChanged is not True:
            logger.info("Call of Duty Message of the Day not updated")

    def Notify(self: Any, data: Dict[str, Any]) -> bool:
        """Report feed updates to the configured Discord webhook."""

        settings: Dict[str, Any] = self.config["discord"]

        payload: Dict[str, Any] = {
            "username": settings["username"],
            "avatar_url": settings["avatarUrl"],
            "embeds": [
                {
                    "title": data["title"],
                    "description": data["description"],
                    "url": data.get("url"),
                    "timestamp": datetime.utcnow().isoformat()
                    if (timestamp := data.get("timestamp")) is None
                    else timestamp,
                    "color": data["color"],
                    "footer": {
                        "text": "Broadcast",
                        "icon_url": "https://i.imgur.com/6CNKsKZ.png",
                    },
                    "image": {"url": data["image"]},
                    "author": {"name": data.get("author")},
                    "fields": data["fields"],
                }
            ],
        }

        return Utility.POST(self, settings["webhookUrl"], payload)

    def SaveHistory(self: Any) -> None:
        """Save the latest feed items to history.json"""

        if self.config.get("debug") is True:
            logger.warning("Debug is active, not saving feed history")

            return

        try:
            with open("history.json", "w+") as file:
                file.write(json.dumps(self.history, indent=4))
        except Exception as e:
            logger.critical(f"Failed to save feed history, {e}")

            exit(1)

        logger.success("Saved feed history")


if __name__ == "__main__":
    try:
        Broadcast.Initialize(Broadcast)
    except KeyboardInterrupt:
        exit()
