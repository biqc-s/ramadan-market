# Troubleshooting: Invalid Token Error

You encountered the following error:
`telegram.error.InvalidToken: The token ... was rejected by the server.`

## Cause
The token you provided (`AAGdPs26bOZ1dvhkG4cq27xs6oOp0iW7ZYk`) is **incomplete**.
A Telegram Bot command always starts with a numeric **Bot ID** followed by a colon.

## Solution
1. Open **BotFather** on Telegram.
2. Copy the **full token**. It should look like this:
   `1234567890:AAGdPs26bOZ1dvhkG4cq27xs6oOp0iW7ZYk`
   *(Notice the number and colon at the beginning)*
3. Open `bot.py` and update the `TOKEN` variable:
   ```python
   TOKEN = "YOUR_FULL_TOKEN_HERE"
   ```
   ```
<<<<<<< SEARCH
4. Run the bot again.
=======
4. Run the bot again.

### AttributeError: `'Updater' object has no attribute...`
This error happens with older versions of `python-telegram-bot` (v20.*) on newer Python versions (3.13+).
**Fix:**
Update the library to the latest version:
```bash
pip install --upgrade python-telegram-bot
```
>>>>>>> REPLACE
