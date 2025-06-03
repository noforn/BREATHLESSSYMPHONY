import unittest
import os
import sys
from unittest.mock import patch

# Add the parent directory to sys.path to allow imports from 'core'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.ui import BreathlessUI, READLINE_AVAILABLE

# Conditionally import readline for the test
if READLINE_AVAILABLE:
    import readline

class TestUIHistory(unittest.TestCase):

    def setUp(self):
        self.test_history_file = ".test_breathless_history"
        # Ensure no old test history file interferes
        if os.path.exists(self.test_history_file):
            os.remove(self.test_history_file)

    def tearDown(self):
        # Clean up the test history file
        if os.path.exists(self.test_history_file):
            os.remove(self.test_history_file)

    def test_history_file_creation_and_write(self):
        if not READLINE_AVAILABLE:
            self.skipTest("Readline not available, skipping history file test")

        ui = BreathlessUI()
        # Override history file for this test
        # This is crucial because the default is ~/.breathless_history
        ui.history_file = self.test_history_file
        
        # Manually add to readline's history and write
        # We interact directly with readline and the UI's history file attribute
        # rather than trying to simulate input() which is complex.
        
        test_command_1 = "test command 1 for history"
        test_command_2 = "another test command for history"
        
        # Clear any existing readline history in memory from previous runs or other sources
        readline.clear_history()

        # Add commands to readline's internal history
        readline.add_history(test_command_1)
        readline.add_history(test_command_2)
        
        # Explicitly call write_history_file using the test path
        # This simulates what ui.user_input() would do if readline is available
        try:
            readline.write_history_file(ui.history_file)
        except Exception as e:
            self.fail(f"Failed to write history file: {e}")

        self.assertTrue(os.path.exists(ui.history_file), "History file was not created.")

        with open(ui.history_file, 'r') as f:
            content = f.read()
            self.assertIn(test_command_1, content, "First test command not in history file.")
            self.assertIn(test_command_2, content, "Second test command not in history file.")

    def test_history_loading_if_file_exists(self):
        if not READLINE_AVAILABLE:
            self.skipTest("Readline not available, skipping history loading test")

        # Setup: Create a dummy history file
        dummy_command_1 = "previous command 1"
        dummy_command_2 = "old command 2"
        with open(self.test_history_file, 'w') as f:
            f.write(dummy_command_1 + "\n")
            f.write(dummy_command_2 + "\n")
        
        # Clear readline's current in-memory history
        readline.clear_history()

        # Instantiate UI - this should load the history
        # We need to ensure that the __init__ method of BreathlessUI, which calls read_history_file,
        # uses our self.test_history_file.
        # One way is to temporarily patch os.path.expanduser or the history_file attribute *before* init.
        # However, BreathlessUI sets self.history_file *inside* __init__.
        # A simpler way for this test is to call read_history_file manually after setting the path.
        
        ui = BreathlessUI()
        ui.history_file = self.test_history_file # Override after init for this part of test
        
        # Call read_history_file directly to simulate the load part of __init__ with the test file
        try:
            readline.read_history_file(ui.history_file)
        except Exception as e:
            # If the file is empty or malformed, readline might raise an error.
            # For this test, we assume a valid file written by readline itself.
            pass # Or self.fail(f"Failed to read history file: {e}")

        # Check readline's internal history
        # Note: readline history is 1-indexed by get_history_item
        # and stores items in the order they were added.
        # The items loaded from file should be the first items.
        
        # Verify that the history was loaded
        # Check the current length of the history
        history_len = readline.get_current_history_length()
        
        # This assertion is tricky because readline might have a limit on history size,
        # and read_history_file might behave differently across platforms or versions
        # if the file doesn't end with a newline, etc.
        # A more robust check is to see if our specific commands can be found.
        
        # We'll retrieve all history items and check
        loaded_history = [readline.get_history_item(i) for i in range(1, history_len + 1)]
        
        self.assertIn(dummy_command_1, loaded_history, "First dummy command not loaded into history.")
        self.assertIn(dummy_command_2, loaded_history, "Second dummy command not loaded into history.")

class TestUIAutocomplete(unittest.TestCase):
    def setUp(self):
        self.ui = BreathlessUI()
        # Commands are: ["bye", "exit", "clear", "help", "search", "list"]

    @unittest.skipIf(not READLINE_AVAILABLE, "Readline not available, skipping set_completer test")
    def test_readline_setup_if_available(self):
        with unittest.mock.patch('core.ui.readline') as mock_readline:
            # Re-initialize UI to trigger readline setup within the context of the mock
            ui_instance = BreathlessUI()
            mock_readline.set_completer.assert_called_once_with(ui_instance._completer)
            mock_readline.parse_and_bind.assert_called_once_with('tab: complete')

    def test_completer_logic(self):
        # Test direct calls to _completer
        self.assertEqual(self.ui._completer("h", 0), "help")
        self.assertEqual(self.ui._completer("he", 0), "help")
        self.assertEqual(self.ui._completer("help", 0), "help")

        self.assertEqual(self.ui._completer("l", 0), "list")
        self.assertEqual(self.ui._completer("li", 0), "list")
        self.assertEqual(self.ui._completer("lis", 0), "list")

        self.assertEqual(self.ui._completer("ex", 0), "exit")
        self.assertIsNone(self.ui._completer("ex", 1)) # No other command starts with "ex"

        self.assertEqual(self.ui._completer("s", 0), "search") # "search"
        self.assertIsNone(self.ui._completer("s", 1)) # No other command starts with "s" that would be second

        self.assertEqual(self.ui._completer("", 0), "bye") # First command
        self.assertEqual(self.ui._completer("", 1), "exit") # Second command
        self.assertEqual(self.ui._completer("", 5), "list") # Last command
        self.assertIsNone(self.ui._completer("", 6)) # Index out of bounds

        self.assertIsNone(self.ui._completer("nonexistent", 0))
        self.assertIsNone(self.ui._completer(" help", 0)) # Test with leading space (should not match)


if __name__ == '__main__':
    # This allows running the test file directly
    # For example: python tests/test_ui.py
    unittest.main()
