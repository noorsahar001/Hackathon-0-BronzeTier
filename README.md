# AI Employee System - Bronze Tier

A file-based digital employee system using Obsidian as a dashboard and Python watchers to monitor Gmail and filesystem for incoming tasks.

## Overview

The Bronze Tier AI Employee system automates the detection and organization of incoming work items. It monitors:
- **Gmail**: Unread important emails
- **Filesystem**: New files dropped into an Inbox folder

When new items are detected, the system creates action files in a central `/Needs_Action` folder that can be reviewed and processed by you or Claude Code.

## System Architecture

```
AI_Employee_Vault/
├── Dashboard.md              # Main overview and status
├── Company_Handbook.md       # Operating rules and guidelines
├── Needs_Action/            # Items requiring attention
├── Done/                    # Completed/archived items
├── Inbox/                   # Drop zone for new files
├── Logs/                    # System logs and activity records
├── Plans/                   # Future plans and strategies
├── base_watcher.py          # Abstract base class for watchers
├── gmail_watcher.py         # Gmail monitoring script
├── filesystem_watcher.py    # Filesystem monitoring script
├── requirements.txt         # Python dependencies
└── .env.example            # Environment configuration template
```

## Features

### Gmail Watcher
- Monitors Gmail for unread important emails every 120 seconds
- Creates action files with email details and suggested actions
- Tracks processed emails to avoid duplicates
- OAuth2 authentication (secure, no password storage)
- DRY_RUN mode for safe testing

### Filesystem Watcher
- Real-time monitoring of /Inbox folder using watchdog
- Automatically copies new files to /Needs_Action
- Creates metadata files with file details
- Handles duplicate filenames gracefully
- Logs all file operations

### Safety Features
- DRY_RUN mode enabled by default
- Comprehensive logging (console + file)
- Error handling with graceful recovery
- No destructive operations (files moved, not deleted)
- Credentials stored securely in environment variables

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Gmail account (for email monitoring)
- Google Cloud project with Gmail API enabled

### Step 1: Install Python Dependencies

```bash
cd AI_Employee_Vault
pip install -r requirements.txt
```

### Step 2: Set Up Gmail API (Optional - only if using Gmail watcher)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON file
5. Save the downloaded file as `credentials.json` in the vault directory

### Step 3: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your settings
# For testing, keep DRY_RUN=true
```

Example `.env` configuration:
```
VAULT_PATH=./AI_Employee_Vault
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
DRY_RUN=true
CHECK_INTERVAL=120
```

### Step 4: First Run - Gmail Authentication

On first run, the Gmail watcher will open a browser for OAuth authentication:

```bash
python gmail_watcher.py
```

- Follow the browser prompts to authorize access
- Token will be saved to `token.json` for future use
- You only need to do this once

## Running the Watchers

### Gmail Watcher

Monitor Gmail for important emails:

```bash
python gmail_watcher.py
```

In DRY_RUN mode, it will log what it would do without creating files.

### Filesystem Watcher

Monitor the Inbox folder for new files:

```bash
python filesystem_watcher.py
```

Drop any file into `/Inbox` and watch it get processed automatically.

### Running Both Watchers

Open two terminal windows and run each watcher in its own window:

**Terminal 1:**
```bash
python gmail_watcher.py
```

**Terminal 2:**
```bash
python filesystem_watcher.py
```

## Testing the System

### Test 1: Filesystem Watcher

1. Start the filesystem watcher
2. Drop a test file into `AI_Employee_Vault/Inbox/`
3. Check `AI_Employee_Vault/Needs_Action/` for the copied file and metadata

### Test 2: Gmail Watcher (DRY_RUN)

1. Mark an email as important in Gmail
2. Start the gmail watcher
3. Check console logs - it should detect the email
4. In DRY_RUN mode, no files are created (safe testing)

### Test 3: Claude Code Integration

1. Open the vault in Obsidian or your text editor
2. Check `Needs_Action/claude_test_task.md`
3. Ask Claude Code to process this task
4. Verify Claude Code can read, write, and move files

## Using with Obsidian

1. Open Obsidian
2. "Open folder as vault" and select `AI_Employee_Vault`
3. Open `Dashboard.md` as your main view
4. Use Obsidian's file explorer to navigate between folders
5. Review items in `/Needs_Action` and move to `/Done` when complete

## Production Deployment

When ready to go live:

1. **Test thoroughly in DRY_RUN mode first**
2. Edit `.env` and set `DRY_RUN=false`
3. Restart the watchers
4. Monitor logs closely for the first few days
5. Review `Company_Handbook.md` and adjust rules as needed

## Folder Structure Explained

### /Needs_Action
Items requiring human attention or Claude Code processing. This is your main work queue.

### /Done
Completed or archived items. Never delete files - move them here instead.

### /Inbox
Drop zone for new files. The filesystem watcher monitors this folder.

### /Logs
System logs and activity records. Each watcher creates its own log file.

### /Plans
Strategic plans and future tasks. Use this for long-term planning.

## Customization

### Adjusting Check Interval

Edit `.env`:
```
CHECK_INTERVAL=300  # Check every 5 minutes instead of 2
```

### Modifying Email Query

Edit `gmail_watcher.py`, line with `query = 'is:unread is:important'`:
```python
query = 'is:unread label:work'  # Only emails with 'work' label
```

### Adding New Watchers

1. Create a new class inheriting from `BaseWatcher`
2. Implement `check_for_updates()` and `create_action_file()`
3. Follow the pattern in `gmail_watcher.py` or `filesystem_watcher.py`

## Troubleshooting

### Gmail Authentication Fails
- Verify `credentials.json` is in the correct location
- Check that Gmail API is enabled in Google Cloud Console
- Delete `token.json` and re-authenticate

### Filesystem Watcher Not Detecting Files
- Verify the watcher is running
- Check that files are being placed in `/Inbox` (not a subfolder)
- Check logs in `/Logs` for error messages

### Permission Errors
- Ensure Python has read/write access to the vault directory
- On Windows, run terminal as administrator if needed

## Security Notes

- Never commit `.env` or `credentials.json` to version control
- Keep `token.json` secure (contains OAuth access token)
- Review `Company_Handbook.md` for security guidelines
- Use DRY_RUN mode when testing with real data

## Next Steps (Silver/Gold Tiers)

Future enhancements could include:
- Automated email responses (with approval workflow)
- Calendar integration
- Slack/Discord monitoring
- Bank account balance checking
- Automated report generation
- Claude Code autonomous processing

## Support

For issues or questions:
1. Check the logs in `/Logs` directory
2. Review `Company_Handbook.md` for operating rules
3. Verify environment configuration in `.env`

## License

This is a personal AI employee system. Modify and use as needed for your own automation needs.

---

**Version**: 1.0  
**Last Updated**: 2026-04-11  
**Status**: Bronze Tier - Operational
