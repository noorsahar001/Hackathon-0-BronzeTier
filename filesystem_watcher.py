"""
Filesystem Watcher
Monitors the /Inbox folder for new files and creates action items.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from base_watcher import BaseWatcher


class InboxFileHandler(FileSystemEventHandler):
    """
    Event handler for filesystem events in the Inbox folder.

    Processes new files dropped into /Inbox by copying them to /Needs_Action
    and creating metadata files.
    """

    def __init__(self, watcher):
        """
        Initialize the file handler.

        Args:
            watcher: Reference to parent FilesystemWatcher instance
        """
        self.watcher = watcher
        super().__init__()

    def on_created(self, event):
        """
        Called when a file or directory is created.

        Args:
            event: FileSystemEvent object
        """
        # Ignore directory creation
        if event.is_directory:
            return

        # Only process file creation events
        if isinstance(event, FileCreatedEvent):
            file_path = Path(event.src_path)
            self.watcher.logger.info(f"New file detected: {file_path.name}")

            # Process the new file
            self.watcher.process_new_file(file_path)


class FilesystemWatcher(BaseWatcher):
    """
    Watches the /Inbox folder for new files.

    When a new file is detected:
    1. Copies it to /Needs_Action
    2. Creates a metadata .md file with file details
    3. Logs the event
    """

    def __init__(self, vault_path: str, check_interval: int = 120):
        """
        Initialize filesystem watcher.

        Args:
            vault_path: Path to AI Employee vault
            check_interval: Not used for watchdog (real-time monitoring)
        """
        super().__init__(vault_path, check_interval)

        # Watchdog observer
        self.observer = None

        self.logger.info("Filesystem watcher initialized")
        self.logger.info(f"Monitoring: {self.inbox_dir}")

    def process_new_file(self, file_path: Path):
        """
        Process a newly detected file in /Inbox.

        Args:
            file_path: Path to the new file
        """
        try:
            # Wait a moment to ensure file is fully written
            # (some apps write files in chunks)
            import time
            time.sleep(0.5)

            # Verify file still exists and is readable
            if not file_path.exists():
                self.logger.warning(f"File disappeared before processing: {file_path.name}")
                return

            # Get file information
            file_size = file_path.stat().st_size
            file_name = file_path.name

            # Skip hidden files and metadata files
            if file_name.startswith('.') or file_name.endswith('.md'):
                self.logger.debug(f"Skipping hidden/metadata file: {file_name}")
                return

            self.logger.info(f"Processing file: {file_name} ({file_size} bytes)")

            # Copy file to /Needs_Action
            destination = self.needs_action_dir / file_name

            # Handle duplicate filenames
            if destination.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name_parts = file_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                else:
                    new_name = f"{file_name}_{timestamp}"
                destination = self.needs_action_dir / new_name
                self.logger.info(f"File exists, renaming to: {new_name}")

            # Copy the file
            shutil.copy2(file_path, destination)
            self.log_action(f"Copied file to Needs_Action", f"{file_name} -> {destination.name}")

            # Create metadata file
            item_data = {
                'original_path': str(file_path),
                'filename': file_name,
                'size': file_size,
                'copied_to': str(destination)
            }

            self.create_action_file(item_data)

        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}", exc_info=True)

    def create_action_file(self, item_data: dict) -> Optional[Path]:
        """
        Create metadata file in /Needs_Action for a new file.

        Args:
            item_data: Dictionary with file details

        Returns:
            Path to created metadata file, or None if creation failed
        """
        try:
            filename = item_data['filename']
            file_size = item_data['size']
            copied_to = item_data['copied_to']

            # Create metadata filename
            metadata_name = f"FILE_{Path(filename).stem}_metadata.md"
            metadata_path = self.needs_action_dir / metadata_name

            # Format file size
            if file_size < 1024:
                size_str = f"{file_size} bytes"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"

            # Create markdown content
            content = f"""# File Action Required

## File Details
- **Original Filename**: {filename}
- **File Size**: {size_str}
- **Detected**: {self.get_timestamp()}
- **Location**: {copied_to}

## File Information
- **Type**: {Path(filename).suffix or 'No extension'}
- **Status**: Pending Review

---

## Suggested Actions
- [ ] Review file contents
- [ ] Determine purpose/category
- [ ] Process or forward as needed
- [ ] Move to Done when complete

## Processing Notes
*Add notes about this file here*

---

## Status
- **Created**: {self.get_timestamp()}
- **Status**: Pending
- **Priority**: Normal

---
*Generated by FilesystemWatcher*
"""

            # Write metadata file
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.log_action(
                f"Created metadata file",
                f"For: {filename}"
            )

            return metadata_path

        except Exception as e:
            self.logger.error(f"Error creating metadata file: {str(e)}", exc_info=True)
            return None

    def check_for_updates(self) -> int:
        """
        Not used for filesystem watcher (uses real-time watchdog instead).

        Returns:
            0 (watchdog handles events in real-time)
        """
        # This method is required by BaseWatcher but not used
        # Watchdog handles events in real-time via callbacks
        return 0

    def run(self):
        """
        Start the filesystem watcher using watchdog.

        Monitors /Inbox in real-time for new files.
        """
        self.logger.info("Starting Filesystem Watcher")
        self.logger.info(f"Monitoring: {self.inbox_dir}")
        self.logger.info("Press Ctrl+C to stop")

        try:
            # Create event handler
            event_handler = InboxFileHandler(self)

            # Create observer
            self.observer = Observer()
            self.observer.schedule(
                event_handler,
                str(self.inbox_dir),
                recursive=False
            )

            # Start observer
            self.observer.start()
            self.logger.info("Filesystem watcher started successfully")

            # Keep running
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Stopping filesystem watcher (user interrupted)")
                self.observer.stop()

            # Wait for observer to finish
            self.observer.join()

        except Exception as e:
            self.logger.critical(f"Fatal error: {str(e)}", exc_info=True)
            if self.observer:
                self.observer.stop()
            raise


def main():
    """Main entry point for filesystem watcher."""
    import sys
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    vault_path = os.getenv('VAULT_PATH', './AI_Employee_Vault')

    print("=" * 60)
    print("Filesystem Watcher - AI Employee System")
    print("=" * 60)
    print(f"Vault Path: {vault_path}")
    print(f"Monitoring: {vault_path}/Inbox")
    print("=" * 60)
    print()

    try:
        watcher = FilesystemWatcher(vault_path=vault_path)
        watcher.run()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
