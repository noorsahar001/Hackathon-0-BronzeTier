"""
Base Watcher Template
Abstract base class for all watcher components in the AI Employee system.
"""

import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional


class BaseWatcher(ABC):
    """
    Abstract base class for watcher components.

    All watchers should inherit from this class and implement:
    - check_for_updates(): Check for new items to process
    - create_action_file(): Create action files in /Needs_Action
    """

    def __init__(self, vault_path: str, check_interval: int = 120):
        """
        Initialize the base watcher.

        Args:
            vault_path: Path to the AI Employee vault directory
            check_interval: Seconds between checks (default: 120)
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval

        # Validate vault path exists
        if not self.vault_path.exists():
            raise ValueError(f"Vault path does not exist: {vault_path}")

        # Set up key directories
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.done_dir = self.vault_path / "Done"
        self.inbox_dir = self.vault_path / "Inbox"
        self.logs_dir = self.vault_path / "Logs"

        # Ensure all directories exist
        for directory in [self.needs_action_dir, self.done_dir,
                         self.inbox_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)

        # Set up logging
        self._setup_logging()

        self.logger.info(f"Initialized {self.__class__.__name__}")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Check interval: {self.check_interval} seconds")

    def _setup_logging(self):
        """Configure logging for this watcher."""
        # Create logger specific to this watcher class
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler - log to vault's Logs directory
        log_file = self.logs_dir / f"{self.__class__.__name__}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    @abstractmethod
    def check_for_updates(self) -> int:
        """
        Check for new items to process.

        This method should be implemented by subclasses to check their
        specific source (Gmail, filesystem, etc.) for new items.

        Returns:
            Number of new items found
        """
        pass

    @abstractmethod
    def create_action_file(self, item_data: dict) -> Optional[Path]:
        """
        Create an action file in /Needs_Action for a new item.

        Args:
            item_data: Dictionary containing item information

        Returns:
            Path to created file, or None if creation failed
        """
        pass

    def get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def get_date_string(self) -> str:
        """Get current date string (YYYY-MM-DD)."""
        return datetime.now().strftime('%Y-%m-%d')

    def run(self):
        """
        Main run loop for the watcher.

        Continuously checks for updates at the specified interval.
        Handles errors gracefully and logs all activity.
        """
        self.logger.info(f"Starting {self.__class__.__name__} run loop")
        self.logger.info(f"Press Ctrl+C to stop")

        try:
            while True:
                try:
                    # Check for updates
                    self.logger.info("Checking for updates...")
                    new_items = self.check_for_updates()

                    if new_items > 0:
                        self.logger.info(f"Found {new_items} new item(s)")
                    else:
                        self.logger.info("No new items found")

                    # Wait before next check
                    self.logger.debug(f"Sleeping for {self.check_interval} seconds")
                    time.sleep(self.check_interval)

                except KeyboardInterrupt:
                    # Re-raise to be caught by outer try/except
                    raise

                except Exception as e:
                    # Log error but continue running
                    self.logger.error(f"Error during check: {str(e)}", exc_info=True)
                    self.logger.info(f"Continuing after error. Next check in {self.check_interval} seconds")
                    time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.logger.info(f"Stopping {self.__class__.__name__} (user interrupted)")

        except Exception as e:
            self.logger.critical(f"Fatal error: {str(e)}", exc_info=True)
            raise

    def log_action(self, action: str, details: str = ""):
        """
        Log an action to both logger and a daily action log file.

        Args:
            action: Description of the action taken
            details: Additional details about the action
        """
        # Log to standard logger
        log_message = f"{action}"
        if details:
            log_message += f" - {details}"
        self.logger.info(log_message)

        # Also append to daily action log
        date_str = self.get_date_string()
        action_log = self.logs_dir / f"actions_{date_str}.log"

        with open(action_log, 'a', encoding='utf-8') as f:
            timestamp = self.get_timestamp()
            f.write(f"[{timestamp}] [{self.__class__.__name__}] {log_message}\n")
