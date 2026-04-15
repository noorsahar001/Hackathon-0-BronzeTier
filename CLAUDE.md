# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is a Bronze Tier AI Employee system that monitors Gmail and filesystem for incoming work items. It uses a watcher-based architecture where Python scripts continuously monitor sources and create action files in a central `/Needs_Action` folder.

## Development Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running Watchers
```bash
# Gmail watcher (polls every 120s by default)
python gmail_watcher.py

# Filesystem watcher (real-time monitoring)
python filesystem_watcher.py
```

### First-Time Gmail Setup
On first run, `gmail_watcher.py` opens a browser for OAuth2 authentication. The token is saved to `token.json` for future use. You need `credentials.json` from Google Cloud Console with Gmail API enabled.

### Configuration
All configuration is in `.env` (copy from `.env.example`):
- `DRY_RUN=true` - CRITICAL: keeps this true during development. When true, watchers log actions but don't create files.
- `CHECK_INTERVAL=120` - seconds between Gmail checks
- `VAULT_PATH` - path to the vault directory

## Architecture

### Watcher Pattern
All watchers inherit from `BaseWatcher` (base_watcher.py), which provides:
- Logging setup (console + file in `/Logs`)
- Directory structure validation
- Run loop with error handling
- Common utilities (timestamps, action logging)

Subclasses must implement:
- `check_for_updates()` - returns count of new items found
- `create_action_file(item_data)` - creates markdown file in `/Needs_Action`

### Two Monitoring Approaches

**GmailWatcher** (gmail_watcher.py):
- Polling-based: calls Gmail API every `CHECK_INTERVAL` seconds
- Query: `is:unread is:important`
- Tracks processed email IDs in `/Logs/processed_emails.txt` to avoid duplicates
- Uses OAuth2 with token refresh
- Respects `DRY_RUN` mode

**FilesystemWatcher** (filesystem_watcher.py):
- Real-time: uses watchdog Observer for instant file detection
- Monitors `/Inbox` folder only (not recursive)
- Copies files to `/Needs_Action` and creates metadata markdown files
- Handles duplicate filenames by appending timestamps
- Ignores hidden files and `.md` files

### Folder Workflow
```
Inbox/ → Needs_Action/ → Done/
```
- **Inbox**: Drop zone for new files (filesystem watcher monitors this)
- **Needs_Action**: Work queue - all action items land here
- **Done**: Archive - NEVER delete files, always move here
- **Logs**: System logs and activity records
- **Plans**: Strategic planning (not used by watchers)

### Critical Operating Rules (from Company_Handbook.md)

When processing items in `/Needs_Action`:
- **Never delete files** - always move to `/Done`
- **Flag payments >$500** - create high-priority action items
- **Never send emails without human approval** - all email actions require confirmation
- **Log every action** - use the watcher's `log_action()` method
- **DRY_RUN must be true during testing** - only set false after explicit authorization

### File Naming Conventions
- Email actions: `EMAIL_{message_id}.md`
- File metadata: `FILE_{filename}_metadata.md`
- Logs: `{WatcherClassName}.log` and `actions_{YYYY-MM-DD}.log`

### Adding New Watchers

1. Create new class inheriting from `BaseWatcher`
2. Implement `check_for_updates()` and `create_action_file()`
3. Use `self.logger` for logging
4. Use `self.needs_action_dir` for output files
5. Call `self.log_action()` for important events
6. Follow the pattern in `gmail_watcher.py` or `filesystem_watcher.py`

## Security Notes

- OAuth2 credentials in `credentials.json` and `token.json` - never commit these
- `.env` contains configuration - never commit (only `.env.example`)
- Gmail API uses readonly scope: `gmail.readonly`
- All sensitive data should use environment variables

## Testing

Always test with `DRY_RUN=true` first. In this mode:
- GmailWatcher logs what it would do but creates no files
- FilesystemWatcher still copies files (it doesn't have DRY_RUN mode)

To test Gmail watcher without creating files, keep `DRY_RUN=true` and check console logs.

## Common Issues

- **Gmail authentication fails**: Delete `token.json` and re-authenticate
- **Filesystem watcher not detecting**: Ensure files are placed directly in `/Inbox`, not subfolders
- **Duplicate processing**: Check `/Logs/processed_emails.txt` for Gmail; filesystem watcher handles duplicates via timestamp suffixes
