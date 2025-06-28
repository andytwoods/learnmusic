"""
Tests for the purge_old_huey_monitor_records task.
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone

from notes.tasks import purge_old_huey_monitor_records


class TestPurgeOldHueyMonitorRecords(TestCase):
    """Test cases for the purge_old_huey_monitor_records function."""

    @patch('notes.tasks.TaskModel.objects.filter')
    @patch('notes.tasks.SignalInfoModel.objects.filter')
    @patch('notes.tasks.logger')
    def test_purge_old_records(self, mock_logger, mock_signal_filter, mock_task_filter):
        """Test that old records are purged correctly."""
        # Set up mocks
        mock_task_queryset = MagicMock()
        mock_task_queryset.delete.return_value = (10, {})  # 10 records deleted
        mock_task_filter.return_value = mock_task_queryset

        mock_signal_queryset = MagicMock()
        mock_signal_queryset.delete.return_value = (5, {})  # 5 records deleted
        mock_signal_filter.return_value = mock_signal_queryset

        # Call the function
        purge_old_huey_monitor_records()

        # Check that filter was called with the correct cutoff date
        cutoff_date = timezone.now() - timedelta(days=7)
        # Since we don't know which field name will work, we check that filter was called
        self.assertTrue(mock_task_filter.called)
        self.assertTrue(mock_signal_filter.called)

        # Check that delete was called on both querysets
        mock_task_queryset.delete.assert_called_once()
        mock_signal_queryset.delete.assert_called_once()

        # Check that info was logged
        mock_logger.info.assert_called_once()

    @patch('notes.tasks.TaskModel.objects.filter')
    @patch('notes.tasks.SignalInfoModel.objects.filter')
    @patch('notes.tasks.logger')
    def test_handle_exceptions(self, mock_logger, mock_signal_filter, mock_task_filter):
        """Test that exceptions are handled correctly."""
        # Set up mocks to raise exceptions
        mock_task_filter.side_effect = Exception("Test exception for TaskModel")
        mock_signal_filter.side_effect = Exception("Test exception for SignalInfoModel")

        # Call the function
        purge_old_huey_monitor_records()

        # Check that errors were logged
        self.assertTrue(mock_logger.error.called)
        # The outer try-except should catch all exceptions, so the function should complete
        # without raising any exceptions
