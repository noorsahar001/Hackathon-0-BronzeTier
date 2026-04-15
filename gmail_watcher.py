"""
Gmail Watcher
Monitors Gmail inbox for unread important emails and creates action items.
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Set, List, Dict
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from base_watcher import BaseWatcher


# Gmail API scopes - readonly access only
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watches Gmail inbox for unread important emails.

    Creates action items in /Needs_Action for each new important email.
    Tracks processed emails to avoid duplicates.
    """

    def __init__(self, vault_path: str, check_interval: int = 120,
                 credentials_path: str = 'credentials.json',
                 token_path: str = 'token.json',
                 dry_run: bool = True):
        """
        Initialize Gmail watcher.

        Args:
            vault_path: Path to AI Employee vault
            check_interval: Seconds between checks (default: 120)
            credentials_path: Path to Gmail API credentials file
            token_path: Path to store OAuth token
            dry_run: If True, only log actions without creating files
        """
        super().__init__(vault_path, check_interval)

        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.dry_run = dry_run

        # Track processed email IDs to avoid duplicates
        self.processed_emails_file = self.logs_dir / 'processed_emails.txt'
        self.processed_emails: Set[str] = self._load_processed_emails()

        # Gmail service (initialized on first check)
        self.service = None

        self.logger.info(f"DRY_RUN mode: {self.dry_run}")
        if self.dry_run:
            self.logger.warning("Running in DRY_RUN mode - no files will be created")

    def _load_processed_emails(self) -> Set[str]:
        """Load set of already-processed email IDs from disk."""
        if self.processed_emails_file.exists():
            with open(self.processed_emails_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_processed_email(self, email_id: str):
        """Save an email ID to the processed list."""
        self.processed_emails.add(email_id)
        with open(self.processed_emails_file, 'a') as f:
            f.write(f"{email_id}\n")

    def _get_gmail_service(self):
        """
        Authenticate and return Gmail API service.

        Uses OAuth2 flow. On first run, opens browser for authentication.
        Token is saved for future use.
        """
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            self.logger.info("Loading existing Gmail token")
            creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                self.logger.info("Refreshing expired Gmail token")
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials file not found: {self.credentials_path}\n"
                        "Please download credentials.json from Google Cloud Console"
                    )

                self.logger.info("Starting OAuth2 flow for Gmail authentication")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for future use
            self.logger.info(f"Saving Gmail token to {self.token_path}")
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def check_for_updates(self) -> int:
        """
        Check Gmail for new unread important emails.

        Returns:
            Number of new emails found
        """
        try:
            # Initialize service if needed
            if self.service is None:
                self.logger.info("Initializing Gmail API service")
                self.service = self._get_gmail_service()

            # Query for unread important emails
            # IMPORTANT label is automatically added by Gmail for priority emails
            query = 'is:unread is:important'
            self.logger.debug(f"Querying Gmail: {query}")

            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=50
            ).execute()

            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} unread important email(s)")

            new_count = 0
            for message in messages:
                msg_id = message['id']

                # Skip if already processed
                if msg_id in self.processed_emails:
                    self.logger.debug(f"Skipping already processed email: {msg_id}")
                    continue

                # Fetch full message details
                msg_data = self._fetch_message_details(msg_id)
                if msg_data:
                    # Create action file
                    action_file = self.create_action_file(msg_data)
                    if action_file:
                        new_count += 1
                        # Mark as processed
                        self._save_processed_email(msg_id)

            return new_count

        except HttpError as error:
            self.logger.error(f"Gmail API error: {error}")
            return 0
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {str(e)}", exc_info=True)
            return 0

    def _fetch_message_details(self, msg_id: str) -> Optional[Dict]:
        """
        Fetch full details for a specific email message.

        Args:
            msg_id: Gmail message ID

        Returns:
            Dictionary with email details, or None if fetch failed
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            header_dict = {h['name']: h['value'] for h in headers}

            # Get email details
            sender = header_dict.get('From', 'Unknown')
            subject = header_dict.get('Subject', 'No Subject')
            date = header_dict.get('Date', 'Unknown')

            # Get snippet (preview text)
            snippet = message.get('snippet', '')

            return {
                'id': msg_id,
                'sender': sender,
                'subject': subject,
                'date': date,
                'snippet': snippet,
                'labels': message.get('labelIds', [])
            }

        except Exception as e:
            self.logger.error(f"Error fetching message {msg_id}: {str(e)}")
            return None

    def create_action_file(self, item_data: dict) -> Optional[Path]:
        """
        Create action file in /Needs_Action for an email.

        Args:
            item_data: Dictionary with email details

        Returns:
            Path to created file, or None if creation failed
        """
        try:
            msg_id = item_data['id']
            sender = item_data['sender']
            subject = item_data['subject']
            date = item_data['date']
            snippet = item_data['snippet']

            # Create filename
            filename = f"EMAIL_{msg_id}.md"
            filepath = self.needs_action_dir / filename

            # Create markdown content
            content = f"""# Email Action Required

## Email Details
- **From**: {sender}
- **Subject**: {subject}
- **Received**: {date}
- **Message ID**: {msg_id}

## Preview
{snippet}

---

## Suggested Actions
- [ ] Read full email in Gmail
- [ ] Draft response
- [ ] Flag if payment over $500 mentioned
- [ ] Archive or move to Done when handled

## Status
- **Created**: {self.get_timestamp()}
- **Status**: Pending Review
- **Priority**: Normal

## Notes
*Add your notes here*

---
*Generated by GmailWatcher*
"""

            if self.dry_run:
                self.logger.info(f"[DRY_RUN] Would create: {filepath}")
                self.logger.info(f"[DRY_RUN] Subject: {subject}")
                self.logger.info(f"[DRY_RUN] From: {sender}")
                return None
            else:
                # Write file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.log_action(
                    f"Created action file for email",
                    f"Subject: {subject}, From: {sender}"
                )
                return filepath

        except Exception as e:
            self.logger.error(f"Error creating action file: {str(e)}", exc_info=True)
            return None


def main():
    """Main entry point for Gmail watcher."""
    import sys
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    vault_path = os.getenv('VAULT_PATH', './AI_Employee_Vault')
    credentials_path = os.getenv('GMAIL_CREDENTIALS_PATH', './credentials.json')
    token_path = os.getenv('GMAIL_TOKEN_PATH', './token.json')
    dry_run = os.getenv('DRY_RUN', 'true').lower() == 'true'
    check_interval = int(os.getenv('CHECK_INTERVAL', '120'))

    print("=" * 60)
    print("Gmail Watcher - AI Employee System")
    print("=" * 60)
    print(f"Vault Path: {vault_path}")
    print(f"DRY_RUN: {dry_run}")
    print(f"Check Interval: {check_interval} seconds")
    print("=" * 60)
    print()

    try:
        watcher = GmailWatcher(
            vault_path=vault_path,
            check_interval=check_interval,
            credentials_path=credentials_path,
            token_path=token_path,
            dry_run=dry_run
        )
        watcher.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
