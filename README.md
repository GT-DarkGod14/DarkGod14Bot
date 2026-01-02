<div align="center">
  <img src="https://raw.githubusercontent.com/GT-DarkGod14/DarkGod14Bot/main/resources/DarkGod14BotProfile.png" alt="DarkGod14Bot Logo" width="500"/>
  <div align="center">
<h1 style="font-size: 3em;">🤖 DarkGod14Bot</h1>
</div>
  <h3>A modular Telegram bot built with Python and SQLAlchemy database</h3>
  
  ![Python](https://img.shields.io/badge/Python-3.9.4-blue?style=fBadge_Grade&logo=python)
  ![PTB](https://img.shields.io/badge/PTB-v13.11-blue?style=Badge_Grade)
  ![License](https://img.shields.io/badge/LICENSE-GPL--3.0-success?style=Badge_Grade)
  ![Maintained](https://img.shields.io/badge/MAINTAINED%3F-YES-brightgreen?style=Badge_Grade)
  ![Built with Python](https://img.shields.io/badge/BUILT%20WITH-PYTHON-blue?style=Badge_Grade&logo=python)
  [![Quality Gate](https://app.codacy.com/project/badge/Grade/972e73015aaa4096bf109a79acae8afb)](https://www.codacy.com/gh/GT-DarkGod14/DarkGod14Bot/dashboard?utm_source=github.com&utm_medium=referral&utm_content=GT-DarkGod14/DarkGod14Bot&utm_campaign=Badge_Grade)
  ![Requirements](https://img.shields.io/badge/PYTHON-99.9%25-blue?style=Badge_Grade&logo=python)
  ![Stars](https://img.shields.io/badge/STARS-0-yellow?style=Badge_Grade&logo=github)
  ![Forks](https://img.shields.io/badge/FORKS-0-lightgrey?style=Badge_Grade&logo=github)
  ![Commits](https://img.shields.io/badge/COMMIT%20ACTIVITY-2%2FMONTH-blue?style=Badge_Grade&logo=github)
  ![Contributors](https://img.shields.io/badge/CONTRIBUTORS-72-green?style=Badge_Grade&logo=github)
  ![Issues](https://img.shields.io/badge/OPEN%20ISSUES-0-red?style=Badge_Grade&logo=github)
  ![Closed Issues](https://img.shields.io/badge/CLOSED%20ISSUES-0-success?style=Badge_Grade&logo=github)
  ![Repo Size](https://img.shields.io/badge/REPO%20SIZE-7.5%20MiB-informational?style=Badge_Grade&logo=github)
</div>

## 🔗 Important Links

<div>

• **Bot link:** [![DarkGod14Bot](https://img.shields.io/badge/🤖%20DarkGod14Bot-0088cc?style=flat-square&logoColor=white)](https://t.me/DarkGod14Bot)

• **Support group:** [![Telegram](https://img.shields.io/badge/%20Support%20Chat-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/DarkGod14BotAltSupport)

• **Recommended federation:** [![GodnessFed](https://img.shields.io/badge/🚫%20GodnessFed-FF4444?style=flat-square&logoColor=white)](https://t.me/AltGodnessFed)

</div>


## ✨ Key Features

- 🔧 **Modular Architecture** - Easy-to-extend module system
- 🛡️ **Robust & Stable** - Built on SaitamaRobot foundation but more optimized
- 🗄️ **Database Integration** - Complete SQLAlchemy database support
- 🌐 **Multi-language** - Support for multiple languages
- ⚡ **High Performance** - Optimized to handle multiple chats efficiently
- 🔒 **Advanced Moderation** - Comprehensive chat management tools
- 🎯 **User-friendly** - Intuitive commands and responses

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.9.4
- PostgreSQL (recommended)
- Telegram Bot Token (get it from [@BotFather](https://t.me/botfather))
- Basic knowledge of Python and databases

### ⚡ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/GT-DarkGod14/DarkGod14Bot.git
   cd DarkGod14Bot
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set up database (PostgreSQL)**
   ```bash
   # For Ubuntu/Debian
   sudo apt-get update && sudo apt-get install postgresql
   sudo su - postgres
   createuser -P -s -e YOUR_USER
   createdb -O YOUR_USER YOUR_DB_NAME
   ```

4. **Configure the bot**
   
   Create a `config.py` file in the `DarkGod14Bot` folder:
   
   ```python
   from DarkGod14Bot.sample_config import Config
   
   class Development(Config):
       OWNER_ID = 123456789  # Your Telegram ID
       OWNER_USERNAME = "YourUsername"  # Your Telegram username
       API_KEY = "your_bot_token_here"  # Bot token from @BotFather
       SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost:5432/database'
       JOIN_LOGGER = '-1001234567890'  # Group chat ID for logging
       USE_JOIN_LOGGER = True
       SUDO_USERS = [123456789]  # List of sudo user IDs
       LOAD = []
       NO_LOAD = ['translation']
   ```

5. **Start the bot**
   ```bash
   python3 -m DarkGod14Bot
   ```

## ⚙️ Configuration Options

### Environment Variables
If you prefer using environment variables instead of `config.py`:

| Variable | Description | Required |
|----------|-------------|----------|
| `API_KEY` | Bot token from BotFather | ✅ |
| `OWNER_ID` | Your Telegram user ID | ✅ |
| `OWNER_USERNAME` | Your Telegram username | ✅ |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | ✅ |
| `JOIN_LOGGER` | Chat ID for join logging | ✅ |
| `USE_JOIN_LOGGER` | Enable/disable join logging (True/False) | ✅ |
| `SUDO_USERS` | Comma-separated sudo user IDs | ✅ |
| `LOAD` | Comma-separated modules to load | ❌ |
| `NO_LOAD` | Comma-separated modules to exclude | ❌ |

### Database URI Format
```
# Replace sqldbtype, username, password, hostname (default: 0.0.0.0), port (e.g., 5432), and dbname.

postgresql://username:password@hostname:port/database_name
```

## 🏗️ Module System

### Creating Custom Modules

1. Create a `.py` file in the `modules/` folder
2. Import the dispatcher:
   ```python
   from DarkGod14Bot import dispatcher
   ```
3. Add your handlers:
   ```python
   dispatcher.add_handler(CommandHandler("mycommand", my_function))
   ```
4. Set module info:
   ```python
   __help__ = "Description of your module commands"
   __mod_name__ = "Module Name"
   ```

### Module Loading

Control which modules load using `LOAD` and `NO_LOAD` in your config:
- Empty `LOAD` list = load all modules
- `NO_LOAD` takes priority over `LOAD`

## 🚨 Important Notes

> **⚠️ Before deploying:**
> - Edit all mentions of `@DarkGod14BotAltSupport` to your own support chat
> - Your code must be open source with a link to your repository in the bot's start message
> - This repository doesn't include technical support for deployment issues

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📈 Statistics

Use `/stats` command (owner only) to get:
- Active users count
- Chat statistics
- Module usage data
- System performance metrics

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Credits & Acknowledgments

This bot is built upon the excellent work of:
- **[PaulSonOfLars](https://github.com/PaulSonOfLars)** - Original creator
- **[AnimeKaizoku](https://github.com/AnimeKaizoku)** - Core contributor  
- **[Astrako](https://github.com/Astrako/AstrakoBot)** - AstrakoBot base

All original credits go to Paul, AnimeKaizoku, and Astrako. Without their efforts, this fork wouldn't exist!

For queries or any issues regarding the bot please open an [issue](https://github.com/GT-DarkGod14/DarkGod14Bot/issues) or visit us at [DarkGod14BotAltSupport](https://t.me/DarkGod14BotAltSupport)
