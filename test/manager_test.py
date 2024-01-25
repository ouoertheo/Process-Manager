import unittest
from unittest.mock import patch, MagicMock
from process_manager.manager import ProcessManager, ProcesNotFoundException
from process_manager.process_model import (
    ProcessDefinitionList,
    Process,
    ProcessDefinition,
)


class TestProcessManager(unittest.TestCase):
    def setUp(self):
        # Create a sample ProcessDefinitionList for testing
        process_def_list_data = {
            "definitions": {
                "process1": {"command": ["echo 'hello'"], "path": "/"},
                "process2": {"command": ["ls"], "path": "/"},
            }
        }
        self.sample_process_def_list = ProcessDefinitionList(**process_def_list_data)

        # Mock loading process definitions
        with patch(
            "process_manager.manager.ProcessManager.load_process_defs",
            return_value=self.sample_process_def_list,
        ):
            self.process_manager = ProcessManager()

    def test_init_processes(self):
        # Ensure that processes are initialized correctly
        self.assertEqual(len(self.process_manager.processes), 2)

    def test_list_processes(self):
        # Ensure that list_processes returns the correct number of processes
        processes = self.process_manager.list_processes()
        self.assertEqual(len(processes), 2)

    def test_get_process_existing(self):
        # Ensure get_process returns the correct process when it exists
        process = self.process_manager.get_process("process1")
        self.assertIsNotNone(process)
        self.assertEqual(process.name, "process1")

    def test_get_process_nonexistent(self):
        # Ensure get_process returns None when the process does not exist
        process = self.process_manager.get_process("nonexistent_process")
        self.assertIsNone(process)

    @patch("subprocess.Popen")
    def test_start_process(self, mock_popen: MagicMock):
        # Ensure start_process starts a process and updates its status
        process = Process(
            name="test_process",
            process=None,
            definition=self.sample_process_def_list.definitions["process1"],
        )
        self.process_manager.start_process(process)
        mock_popen.assert_called_once()
        self.assertEqual(process.status, "running")
        self.assertIsNotNone(process.process)

    @patch("psutil.Process")
    def test_stop_process(self, mock_psutil_process):
        # Ensure stop_process stops a process and updates its status
        process = Process(
            name="test_process",
            process=MagicMock(),
            definition=self.sample_process_def_list.definitions["process1"],
        )
        self.process_manager.stop_process(process)
        mock_psutil_process.assert_called_once()
        self.assertEqual(process.status, "stopped")
        self.assertIsNone(process.process)

    @patch("subprocess.Popen")
    def test_start_process_logging(self, mock_popen: MagicMock):
        # Ensure start_process_logging updates process logs
        process = Process(
            name="test_process1",
            process=None,
            definition=self.sample_process_def_list.definitions["process1"],
        )

        # Create a MagicMock object for the process.stdout
        mock_stdout = MagicMock()

        # Create a MagicMock object for the process
        mock_popen_instance = MagicMock(stdout=mock_stdout)

        # Mock the subprocess.Popen to return the MagicMock process instance
        mock_popen.return_value = mock_popen_instance

        # Start the process
        self.process_manager.start_process(process)

        # Configure the mocked process.stdout to return a log line
        mock_stdout.readline.return_value = "log_line"

        # Call the start_process_logging method
        self.process_manager.poll_process(process)

        # Assertions
        self.assertEqual(process.status, "stopped")
        self.assertEqual(process.logs, ["log_line"])
        self.assertEqual(process.new_log_count, 8)  # Length of "log_line"

    @patch("subprocess.Popen")
    def test_get_process_logs_existing(self, mock_popen: MagicMock):
        # Ensure get_process_logs returns the correct logs when the process exists
        process = Process(
            name="test_process1",
            process=MagicMock(),
            definition=self.sample_process_def_list.definitions["process1"],
        )
        self.process_manager.start_process(process)
        process.logs = ["log1", "log2"]
        process.new_log_count = 10
        logs, new_log_count = self.process_manager.get_process_logs(process)
        self.assertEqual(logs, ["log2", "log1"])  # Reversed order
        self.assertEqual(new_log_count, 10)
        self.assertEqual(process.new_log_count, 0)

    def test_get_process_logs_nonexistent(self):
        # Ensure get_process_logs returns empty logs when the process does not exist
        process = Process(
            name="nonexistent_process",
            process=None,
            definition=self.sample_process_def_list.definitions["process1"],
        )
        logs, new_log_count = self.process_manager.get_process_logs(process)
        self.assertEqual(logs, [])
        self.assertEqual(new_log_count, 0)

    def test_dump_process_defs(self):
        # Ensure dump_process_defs writes the correct data to the file
        filename = "test_processes.json"
        with patch("builtins.open", create=True) as mock_open:
            self.process_manager.dump_process_defs(self.sample_process_def_list)
            mock_open.assert_called_once_with(filename, "w")
            mock_open.return_value.write.assert_called_once_with(
                self.sample_process_def_list.model_dump_json(indent=2)
            )

    def test_load_process_defs(self):
        # Ensure load_process_defs reads the correct data from the file
        filename = "test_processes.json"
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = (
                '{"definitions": {}}'
            )
            process_defs = self.process_manager.load_process_defs()
            mock_open.assert_called_once_with(filename)
            self.assertIsInstance(process_defs, ProcessDefinitionList)


if __name__ == "__main__":
    unittest.main()
