# Discord Logging Bot

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Disnake](https://img.shields.io/badge/Disnake-2.8+-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)

A comprehensive Discord bot for server activity logging with customizable settings and multi-language support.

## Features

- **Detailed Activity Tracking**
  - Message edits/deletes
  - Voice channel events
  - Member joins/leaves/bans
  - Channel/thread modifications
  - Reaction changes
  - Auto-moderation actions

- **Customizable Logging**
  - Per-category toggles (messages, voice, server, etc.)
  - Configurable log channel
  - Granular event type control

- **Multi-language Support**
  - English and Russian included
  - Easy to add new languages

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Discord bot token

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/discord-logging-bot.git
   cd discord-logging-bot
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   ```   
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   ```bash
   cp env.example .env
   # Edit .env with your credentials
   ```

4. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

Use the `/settings` command to configure:

```
/settings logging enable      - Enable logging
/settings channel #logs       - Set log channel
/settings language            - Set bot language
```


## License

MIT License - See [LICENSE](LICENSE) for details.