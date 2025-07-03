import json
import os
import traceback
from typing import List

from PySide6.QtWidgets import QFileDialog, QMessageBox

from models.cue_model import Cue
from models.database_model import CueDatabase


class ShowManager:
    def __init__(self, main_window, db_path=None):
        self.main_window = main_window  # Reference to MainWindow
        self.cue_table_view = None
        self.led_panel = None
        self.db_path = db_path
        self.db = CueDatabase(db_path) if db_path else None

    def set_components(self, cue_table, led_panel):
        """Set the required UI components after they're created"""
        self.cue_table_view = cue_table
        self.led_panel = led_panel

    def save_show_as(self):
        """Saves the current show to a JSON file with a "Save As" dialog."""
        print("Saving show as...")
        try:
            # Open "Save As" dialog
            filepath, _ = QFileDialog.getSaveFileName(self.main_window, "Save Show As", "", "JSON Files (*.json)")
            if not filepath:
                return  # User cancelled the dialog

            # Ensure .json extension if not provided
            if not filepath.lower().endswith(".json"):
                filepath += ".json"

            cues = self._get_cues_from_table()
            if not cues:
                raise ValueError("No cues to save.")

            # Convert cue lists to dictionaries with named fields
            cue_dicts = []
            for cue in cues:
                cue_dict = {
                    "cue_number": cue[0],
                    "cue_type": cue[1],
                    "outputs": cue[2],
                    "delay": cue[3],
                    "execute_time": cue[4]
                }
                # Add duration if it exists
                if len(cue) > 5:
                    cue_dict["duration"] = cue[5]
                cue_dicts.append(cue_dict)

            # Save to JSON file
            with open(filepath, 'w') as f:
                json.dump(cue_dicts, f, indent=4)

            QMessageBox.information(self.main_window, "Save Successful", f"Show saved to {filepath}")

        except Exception as e:
            self._handle_error(f"Error saving show: {e}")

    def _parse_outputs(self, outputs_str):
        """Parses the outputs string into a list of integers."""
        try:
            if outputs_str:  # Check if the string is not empty
                return [int(x.strip()) for x in outputs_str.split(',')]
            else:
                return []  # Return empty list if string is empty
        except (ValueError, AttributeError):  # Handle invalid output strings
            return []

    def load_show(self):
        """Loads a show from a JSON file."""
        print("Loading show...")
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Load Show",
                "",
                "JSON Files (*.json)"
            )
            if not filepath:
                return  # User cancelled

            with open(filepath, 'r') as f:
                cue_dicts = json.load(f)

            # Convert dictionary data back to list format
            cues = []
            for cue_dict in cue_dicts:
                cue = [
                    cue_dict["cue_number"],
                    cue_dict["cue_type"],
                    cue_dict["outputs"],
                    cue_dict["delay"],
                    cue_dict["execute_time"]
                ]
                # Add duration if it exists
                if "duration" in cue_dict:
                    cue.append(cue_dict["duration"])
                cues.append(cue)

            # Clear existing cues
            self.cue_table_view.model.beginResetModel()
            self.cue_table_view.model._data = []
            self.cue_table_view.model.endResetModel()

            # Update with new cues
            self._update_cue_table(cues)
            self.led_panel.updateFromCueData(cues, force_refresh=True)

            QMessageBox.information(self.main_window, "Load Successful", "Show loaded successfully!")
        except Exception as e:
            self._handle_error(f"Error loading show: {e}")

    def export_show(self):
        """Exports the current show to a CSV file."""
        print("Exporting show...")
        try:
            filepath, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Export Show",
                "",
                "CSV Files (*.csv)"
            )
            if not filepath:
                return  # User cancelled

            cues = self._get_cues_from_table()
            if not cues:
                raise ValueError("No cues to export.")

            # Ensure .csv extension if not provided
            if not filepath.lower().endswith(".csv"):
                filepath += ".csv"

            # Write to CSV file
            import csv
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write header row
                writer.writerow(['Cue Number', 'Cue Type', 'Outputs', 'Delay', 'Execute Time'])

                # Write cue data
                for cue in cues:
                    # Create a row with all possible fields
                    row = list(cue)  # Convert tuple to list if necessary
                    # Ensure row has 6 elements (pad with empty strings if needed)
                    while len(row) < 5:
                        row.append('')
                    writer.writerow(row)

            QMessageBox.information(self.main_window, "Export Successful", f"Show exported to {filepath}")
        except Exception as e:
            self._handle_error(f"Error exporting show: {e}")

    def import_show(self):
        """Imports a show from a CSV file."""
        print("Importing show...")
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Import Show",
                "",
                "CSV Files (*.csv)"
            )
            if not filepath:
                return  # User cancelled

            # Read from CSV file
            import csv
            cues = []
            with open(filepath, 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header row
                for row in reader:
                    # Remove any empty strings from the end of the row
                    while row and row[-1] == '':
                        row.pop()
                    if row:  # Only add non-empty rows
                        cues.append(row)

            if not cues:
                raise ValueError("No cues found in the CSV file.")

            # Clear existing cues
            self.cue_table_view.model.beginResetModel()
            self.cue_table_view.model._data = []
            self.cue_table_view.model.endResetModel()

            # Update with new cues
            self._update_cue_table(cues)
            self.led_panel.updateFromCueData(cues, force_refresh=True)

            QMessageBox.information(self.main_window, "Import Successful", f"Show imported from {filepath}")
        except Exception as e:
            self._handle_error(f"Error importing show: {e}")

    def _get_cues_from_table(self) -> List[Cue]:
        """Retrieves cue data from the cue table."""
        try:
            return self.cue_table_view.model._data.copy()  # Access data directly for now
        except Exception as e:
            self._handle_error(f"Error getting cues from table: {e}")
            return []

    def _update_cue_table(self, cues: List):
        """Updates the cue table with the given cue data."""
        try:
            table_model = self.cue_table_view.model
            table_model.beginResetModel()
            table_model._data = cues  # Update the model's data directly
            table_model.endResetModel()
        except Exception as e:
            self._handle_error(f"Error updating cue table: {e}")

    def _handle_error(self, message: str):
        """Handles errors during show management operations."""
        print(f"Error: {message}")
        traceback.print_exc()
        QMessageBox.critical(self.main_window, "Error", message)