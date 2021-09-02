# Broadcast

Broadcast is a Call of Duty feed watcher that reports the news via Discord.

Supported Feeds:

-   [Call of Duty Blog](https://www.callofduty.com/blog)
-   [Call of Duty Companion App](https://www.callofduty.com/app) Message of the Day

<p align="center">
    <img src="https://i.imgur.com/hyzSXYi.png" draggable="false">
</p>

## Usage

Open `config_example.json` and provide the configurable values, then save and rename the file to `config.json`.

Broadcast is designed to be ran using a task scheduler, such as [cron](https://crontab.guru/).

```
python broadcast.py
```
