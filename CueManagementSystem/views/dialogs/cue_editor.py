import traceback
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QPushButton,
                               QHBoxLayout, QWidget, QLabel, QSpinBox, QComboBox,
                               QGridLayout, QDoubleSpinBox, QMessageBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize, QTimer


class EmptyableDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._allowEmpty = True
        self.setSpecialValueText("")

    def textFromValue(self, value):
        if value == 0.0 and self._allowEmpty:
            return ""
        # Format with 3 decimal places
        return f"{value:.3f}".rstrip('0').rstrip('.')

    def valueFromText(self, text):
        if text == "":
            return 0
        return float(text)

    # Handle keyboard events to allow clearing the field
    def keyPressEvent(self, event):
        # Allow clearing the field with Delete or Backspace
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace) and self.value() == 0:
            self.clear()
        else:
            super().keyPressEvent(event)

class CueEditorDialog(QDialog):
    cue_edited = Signal(dict)

    def __init__(self, parent=None, existing_cues=None, edit_cue=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Cue")
        self.existing_cues = existing_cues if existing_cues else []
        self.edit_cue = edit_cue
        self._validator_connected = False
        self._outputs_connected = False
        self._is_initializing = True

        self.init_ui()

        # Set dark theme for dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
            }
        """)
    
        # If edit_cue is provided, populate the fields with its data
        if self.edit_cue:
            self._populate_fields_from_cue()
        else:
            # Set the next available cue number
            self._set_next_available_cue_number()

        # Mark initialization as complete
        self._is_initializing = False

        # Now do a single, clean update of the output spinboxes
        self._update_output_spinboxes(self.cue_type.currentText())

    def init_ui(self, doublespinbox_style=None):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # First row container (Cue # and Type)
        first_row_container = QWidget()
        first_row_container.setFixedHeight(40)
        first_row_layout = QHBoxLayout(first_row_container)
        first_row_layout.setContentsMargins(20, 0, 20, 0)

        # Create a grid layout for labels and inputs
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignCenter)

        # Store run-specific widgets
        self.run_fields = []

        # Cue Number label and input
        cue_num_label = QLabel("Cue #:")
        cue_num_label.setStyleSheet("color: white; font-size: 12px;")

        self.cue_number = QSpinBox()
        self.cue_number.setRange(1, 1000)
        self.cue_number.setValue(1)
        spinbox_style = """
            QSpinBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 50px;
                max-width: 50px;
                min-height: 15px;
                font-size: 12px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4d4d4d;
            }
        """
        doublespinbox_style = """
            QDoubleSpinBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 44px;
                max-width: 44px;
                min-height: 15px;
                font-size: 12px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 16px;
                border: none;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #4d4d4d;
            }
        """

        self.cue_number.setStyleSheet(spinbox_style)
        self.cue_number.setAlignment(Qt.AlignCenter)
        self.cue_number.setButtonSymbols(QSpinBox.UpDownArrows)
        self.cue_number.setKeyboardTracking(True)

        # Cue Type label and combobox
        cue_type_label = QLabel("Type:")
        cue_type_label.setStyleSheet("color: white; font-size: 12px;")

        self.cue_type = QComboBox()
        self.cue_type.addItems(["SINGLE SHOT", "DOUBLE SHOT", "SINGLE RUN", "DOUBLE RUN"])
        self.cue_type.currentTextChanged.connect(self._update_run_fields)
        self.cue_type.currentTextChanged.connect(self._update_output_spinboxes)
        combobox_style = """
            QComboBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
                max-width: 100px;
                min-height: 15px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                margin-right: 5px;
            }
            QComboBox:on {
                border: 1px solid #777777;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: white;
                selection-background-color: #4d4d4d;
                selection-color: white;
                border: 1px solid #555555;
            }
        """
        self.cue_type.setStyleSheet(combobox_style)

        # Add first row widgets to grid
        self.grid_layout.addWidget(cue_num_label, 0, 0)
        self.grid_layout.addWidget(self.cue_number, 0, 1)
        self.grid_layout.addWidget(cue_type_label, 0, 2)
        self.grid_layout.addWidget(self.cue_type, 0, 3)

        # Add grid to first row container with stretches
        first_row_layout.addStretch()
        first_row_layout.addLayout(self.grid_layout)
        first_row_layout.addStretch()
        main_layout.addWidget(first_row_container)

        # Second row container (Outputs, Delay, Time)
        second_row_container = QWidget()
        second_row_container.setFixedHeight(40)  # Set fixed height
        second_row_layout = QHBoxLayout(second_row_container)
        second_row_layout.setContentsMargins(20, 10, 20, 0)  # Add top margin for spacing

        # Second Row Labels and Inputs
        self.outputs_label = QLabel("# of Out:")
        self.outputs_label.setStyleSheet("color: white; font-size: 12px;")
        self.outputs_label.setVisible(False)  # Initially hidden

        self.num_outputs = QSpinBox()
        self.num_outputs.setRange(1, 100)
        self.num_outputs.setValue(1)
        self.num_outputs.setStyleSheet(spinbox_style)
        self.num_outputs.setAlignment(Qt.AlignCenter)
        self.num_outputs.setButtonSymbols(QSpinBox.UpDownArrows)
        self.num_outputs.setKeyboardTracking(True)
        self.num_outputs.setVisible(False)  # Initially hidden

        self.delay_label = QLabel("Delay:")
        self.delay_label.setStyleSheet("color: white; font-size: 12px;")
        self.delay_label.setVisible(False)  # Initially hidden

        self.delay = EmptyableDoubleSpinBox()  # Using custom spinbox
        self.delay.setRange(0, 1000)
        self.delay.setSingleStep(0.05)
        self.delay.setMaximum(99999.99)
        self.delay.setDecimals(3)
        self.delay.setStyleSheet(doublespinbox_style)
        self.delay.setAlignment(Qt.AlignCenter)
        self.delay.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.delay.setKeyboardTracking(True)
        self.delay.setValue(0)
        self.delay.setVisible(False)

        self.execute_label = QLabel("Time:")
        self.execute_label.setStyleSheet("color: white; font-size: 12px;")

        self.execute_time = EmptyableDoubleSpinBox()  # Using custom spinbox
        self.execute_time.setRange(0, 1000)
        self.execute_time.setSingleStep(0.1)
        self.execute_time.setMaximum(99999.99)
        self.execute_time.setDecimals(3)
        self.execute_time.setStyleSheet(doublespinbox_style)
        self.execute_time.setAlignment(Qt.AlignCenter)
        self.execute_time.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        self.execute_time.setKeyboardTracking(True)
        self.execute_time.setValue(0)

        # Create horizontal layout for second row
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        input_layout.setAlignment(Qt.AlignCenter)

        # Add widgets to input layout
        input_layout.addWidget(self.outputs_label)
        input_layout.addWidget(self.num_outputs)
        input_layout.addWidget(self.delay_label)
        input_layout.addWidget(self.delay)
        input_layout.addWidget(self.execute_label)
        input_layout.addWidget(self.execute_time)

        # Add input layout to second row container with stretches
        second_row_layout.addStretch()
        second_row_layout.addLayout(input_layout)
        second_row_layout.addStretch()

        main_layout.addWidget(second_row_container)

        # Middle container (content area)
        self.middle_container = QWidget()
        self.middle_container.setStyleSheet("""
            QWidget {
                background-color: #252525;
                border: 1px solid #333333;
                border-radius: 4px;
                margin: 10px;
            }
        """)
        self.middle_layout = QVBoxLayout(self.middle_container)  # Define middle_layout here
        self.middle_layout.setSpacing(10)
        self.middle_layout.setContentsMargins(10, 10, 10, 10)

        # Create a widget to hold output spinboxes
        self.outputs_container = QWidget()
        self.outputs_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.outputs_layout = QGridLayout(self.outputs_container)
        self.outputs_layout.setSpacing(10)
        self.outputs_layout.setAlignment(Qt.AlignCenter)

        # Add outputs container to middle layout
        self.middle_layout.addWidget(self.outputs_container)
        self.output_spinboxes = []  # Initialize output_spinboxes list

        main_layout.addWidget(self.middle_container, 4)  # Stretch factor for middle container

        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(10)

        # Center layout for buttons
        center_layout = QHBoxLayout()
        center_layout.setSpacing(10)

        # Cancel button
        cancel_button = QPushButton("CANCEL")
        cancel_button.setObjectName("cancelButton")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #cc0000;
                color: white;
                border: 2px solid black;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 80px;
                max-width: 80px;
                min-height: 35px;
                max-height: 35px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff0000;
                border: 2px solid #555;
            }
            QPushButton:pressed {
                background-color: #990000;
                padding-top: 7px;
                padding-bottom: 3px;
                border: 2px solid black;
            }
        """)
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.clicked.connect(self.reject)

        # Save button
        save_button = QPushButton("SAVE")
        save_button.setObjectName("saveButton")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: 2px solid black;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 80px;
                max-width: 80px;
                min-height: 35px;
                max-height: 35px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
                border: 2px solid #555;
            }
            QPushButton:pressed {
                background-color: #083777;
                padding-top: 7px;
                padding-bottom: 3px;
                border: 2px solid black;
            }
        """)
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self._validate_and_accept)

        # Add buttons to center layout
        center_layout.addWidget(cancel_button)
        center_layout.addWidget(save_button)

        # Add center layout to button layout with stretches on both sides
        button_layout.addStretch()
        button_layout.addLayout(center_layout)
        button_layout.addStretch()

        main_layout.addWidget(button_container)

        # Set dialog size
        self.setFixedSize(1000, 500)

        # Initialize run fields based on initial cue type
        self._update_run_fields(self.cue_type.currentText())

        # Set a larger initial size for the dialog
        self.resize(700, 500)  # Width: 700px, Height: 500px

    def _validate_and_accept(self):
        """Validate inputs before accepting"""
        try:
            cue_data = self._collect_cue_data()
            if self._validate_cue(cue_data):
                self.cue_edited.emit(cue_data)
                self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))

    def _collect_cue_data(self) -> dict:
        """Collect all cue data from form"""
        cue_type = self.cue_type.currentText()
        cue_data = {
            "cue_number": self.cue_number.value(),
            "cue_type": cue_type,
            "execute_time": self.execute_time.value()
        }

        # Add run-specific data if applicable
        if "RUN" in cue_type:
            cue_data["num_outputs"] = self.num_outputs.value()
            cue_data["delay"] = self.delay.value()

        return cue_data

    def _update_run_fields(self, cue_type):
        """Update visibility of run-specific fields based on cue type"""
        is_run = "RUN" in cue_type
        is_double_run = "DOUBLE RUN" in cue_type
        is_double = "DOUBLE" in cue_type

        # Show/hide run-specific widgets
        self.outputs_label.setVisible(is_run)
        self.num_outputs.setVisible(is_run)
        self.delay_label.setVisible(is_run)
        self.delay.setVisible(is_run)

        # Skip additional processing during initialization to prevent multiple updates
        if hasattr(self, '_is_initializing') and self._is_initializing:
            return

        # Reset number of outputs based on the cue type
        if is_double_run:
            # Set default value to 2 for double run
            self.num_outputs.setValue(4)
            # Set step to 2 for double run
            self.num_outputs.setSingleStep(2)
        elif is_run:  # SINGLE RUN
            # Set default value to 1 for single run
            self.num_outputs.setValue(2)
            # Reset to single step for SINGLE RUN
            self.num_outputs.setSingleStep(1)

        # Handle even numbers for DOUBLE RUN
        if is_double_run:
            # Ensure current value is even (minimum 2)
            current_value = self.num_outputs.value()
            if current_value < 2:
                self.num_outputs.setValue(2)
            elif current_value % 2 != 0:
                # Make it even by adding 1
                self.num_outputs.setValue(current_value + 1)

        # Handle connections for validators and output updates
        try:
            # For DOUBLE RUN: manage validator connection
            if is_double_run and not self._validator_connected:
                self.num_outputs.valueChanged.connect(self._validate_even_number)
                self._validator_connected = True
            elif not is_double_run and self._validator_connected:
                try:
                    self.num_outputs.valueChanged.disconnect(self._validate_even_number)
                except TypeError:
                    pass  # Already disconnected
                self._validator_connected = False

            # For RUN types: manage outputs connection
            if is_run and not self._outputs_connected:
                self.num_outputs.valueChanged.connect(
                    lambda: self._update_output_spinboxes(self.cue_type.currentText())
                )
                self._outputs_connected = True
            elif not is_run and self._outputs_connected:
                try:
                    # Disconnect all connections to valueChanged
                    self.num_outputs.valueChanged.disconnect()
                    self._outputs_connected = False
                    # Reconnect the validator if needed
                    if is_double_run:
                        self.num_outputs.valueChanged.connect(self._validate_even_number)
                        self._validator_connected = True
                except TypeError:
                    pass  # Already disconnected
        except Exception as e:
            print(f"Error managing signal connections: {e}")
            import traceback
            traceback.print_exc()

        # Set fixed minimum size for the grid to prevent shifting
        if not is_run:
            # We need to ensure the grid keeps its size even when widgets are hidden
            # Find the grid layout and set a minimum width
            second_row_grid = self.execute_label.parentWidget().layout()
            if hasattr(second_row_grid, 'parentWidget') and second_row_grid.parentWidget():
                # Calculate width including all widgets
                total_width = (self.outputs_label.sizeHint().width() +
                               self.num_outputs.sizeHint().width() +
                               self.delay_label.sizeHint().width() +
                               self.delay.sizeHint().width() +
                               self.execute_label.sizeHint().width() +
                               self.execute_time.sizeHint().width() +
                               30)  # Add spacing

                # Set minimum width to prevent layout shifts
                second_row_grid.parentWidget().setMinimumWidth(total_width)

        # Only update output spinboxes if not during initialization
        if not hasattr(self, '_is_initializing') or not self._is_initializing:
            self._update_output_spinboxes(cue_type)

    def _validate_even_number(self, value):
        """Ensure value is even for DOUBLE RUN"""
        if "DOUBLE RUN" in self.cue_type.currentText() and value % 2 != 0:
            # Force to next even number
            self.num_outputs.setValue(value + 1)
            return

    def _update_output_spinboxes(self, cue_type):
        """Update the output spinboxes based on cue type and number of outputs"""
        # First, ensure we clear all existing spinboxes
        self._clear_output_spinboxes()
        
        # Give the UI a moment to process deletions
        QTimer.singleShot(0, lambda: self._create_new_spinboxes(cue_type))
    
    def _create_new_spinboxes(self, cue_type):
        """Create new spinboxes after clearing old ones"""
        is_run = "RUN" in cue_type
        is_double = "DOUBLE" in cue_type

        # Determine number of outputs
        num_outputs = 2  # Default for SINGLE SHOT

        if is_double and not is_run:  # DOUBLE SHOT
            num_outputs = 4
        elif is_run:  # RUN types
            num_outputs = self.num_outputs.value()

        # Create spinboxes
        self._create_output_spinboxes(num_outputs, cue_type)
        
        # Set output values if edit_cue contains parsed values
        if hasattr(self, 'edit_cue') and self.edit_cue and '_parsed_output_values' in self.edit_cue:
            output_values = self.edit_cue['_parsed_output_values']
            for i, value in enumerate(output_values):
                if i < len(self.output_spinboxes):
                    try:
                        # output_spinboxes contains tuples of (label, spinbox)
                        _, spinbox = self.output_spinboxes[i]
                        spinbox.setValue(int(value) if value.is_integer() else value)
                    except (ValueError, TypeError, AttributeError) as e:
                        print(f"Could not set output value: {value} - {str(e)}")

    def _clear_output_spinboxes(self):
        """Clear all output spinboxes from the layout"""
        # Remove all widgets from the layout
        while self.outputs_layout.count():
            item = self.outputs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # If the item is a layout, we need to clear it recursively
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                    elif child.layout():
                        # Handle nested layouts
                        while child.layout().count():
                            grandchild = child.layout().takeAt(0)
                            if grandchild.widget():
                                grandchild.widget().deleteLater()
    
        # Also, remove all direct children of the outputs_container
        for child in self.outputs_container.findChildren(QWidget):
            if child != self.outputs_container and child.parent() == self.outputs_container:
                child.deleteLater()

        # Clear the list of spinboxes
        self.output_spinboxes = []

    def _create_output_spinboxes(self, num_outputs, cue_type):
        """Create and arrange output spinboxes based on cue type"""
        is_run = "RUN" in cue_type
        is_double = "DOUBLE" in cue_type

        # Match the styling from the top containers
        label_style = """
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
                padding-right: 5px;
                min-width: 80px;
            }
        """

        spinbox_style = """
            QSpinBox {
                background-color: #3d3d3d;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 50px;
                min-height: 15px;
                font-size: 14px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 16px;
                border: none;
                background-color: #4d4d4d;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #5d5d5d;
            }
            QSpinBox::up-arrow {
                image: url(:/icons/up_arrow.png);
                width: 10px;
                height: 10px;
            }
            QSpinBox::down-arrow {
                image: url(:/icons/down_arrow.png);
                width: 10px;
                height: 10px;
            }
        """

        # Clear existing output spinboxes list (no need to clear the layout again)
        self.output_spinboxes = []

        # Determine layout configuration
        if is_double and is_run:  # DOUBLE RUN
            # Create a central container widget to hold all columns
            central_container = QWidget()
            central_layout = QHBoxLayout(central_container)
            central_layout.setSpacing(30)
            central_layout.setContentsMargins(5, 5, 5, 5)
            central_layout.setAlignment(Qt.AlignCenter)

            # Configure for pairs of outputs
            max_pairs_per_column = 4  # 4 pairs (8 outputs) per column

            # Calculate how many columns we need
            num_pairs = num_outputs // 2
            num_columns = (num_pairs + max_pairs_per_column - 1) // max_pairs_per_column

            # Create columns
            for col in range(num_columns):
                # Create a column container
                column_container = QWidget()
                column_layout = QVBoxLayout(column_container)
                column_layout.setSpacing(15)
                column_layout.setContentsMargins(0, 0, 0, 0)
                column_layout.setAlignment(Qt.AlignTop)

                # Calculate start and end pair indices for this column
                start_pair_idx = col * max_pairs_per_column
                end_pair_idx = min(start_pair_idx + max_pairs_per_column, num_pairs)

                # Add pairs to this column
                for pair_idx in range(start_pair_idx, end_pair_idx):
                    # Create a container for each pair row
                    pair_container = QWidget()
                    pair_layout = QHBoxLayout(pair_container)
                    pair_layout.setSpacing(10)
                    pair_layout.setContentsMargins(5, 5, 5, 5)

                    # Create label for the pair
                    label = QLabel(f"Pair {pair_idx + 1}:")
                    label.setStyleSheet(label_style)
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    pair_layout.addWidget(label)

                    # Create a container for the spinboxes
                    spinboxes_container = QWidget()
                    spinboxes_layout = QHBoxLayout(spinboxes_container)
                    spinboxes_layout.setSpacing(10)
                    spinboxes_layout.setContentsMargins(0, 0, 0, 0)

                    # Create both spinboxes for this pair
                    for offset in range(2):
                        i = pair_idx * 2 + offset
                        spinbox = QSpinBox()
                        spinbox.setRange(1, 1000)
                        spinbox.setValue(i + 1)
                        spinbox.setStyleSheet(spinbox_style)
                        spinbox.setAlignment(Qt.AlignCenter)
                        spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

                        # Add spinbox to container
                        spinboxes_layout.addWidget(spinbox)

                        # Store reference to label and spinbox
                        self.output_spinboxes.append((label, spinbox))

                    # Add spinboxes container to pair layout
                    pair_layout.addWidget(spinboxes_container)

                    # Add the pair container to the column
                    column_layout.addWidget(pair_container)

                # Add column to central container
                central_layout.addWidget(column_container)

            # Add the central container to the main layout
            self.outputs_layout.addWidget(central_container, 0, 0, alignment=Qt.AlignCenter)

        elif is_run:  # SINGLE RUN
            # Create a central container widget to hold all columns
            central_container = QWidget()
            central_layout = QHBoxLayout(central_container)
            central_layout.setSpacing(30)
            central_layout.setContentsMargins(5, 5, 5, 5)
            central_layout.setAlignment(Qt.AlignCenter)

            # Calculate layout configuration
            max_rows_per_column = 3
            num_columns = (num_outputs + max_rows_per_column - 1) // max_rows_per_column

            # Create columns
            for col in range(num_columns):
                # Create a column container
                column_container = QWidget()
                column_layout = QVBoxLayout(column_container)
                column_layout.setSpacing(15)
                column_layout.setContentsMargins(0, 0, 0, 0)
                column_layout.setAlignment(Qt.AlignTop)

                # Calculate start and end indices for this column
                start_idx = col * max_rows_per_column
                end_idx = min(start_idx + max_rows_per_column, num_outputs)

                # Add outputs to this column
                for i in range(start_idx, end_idx):
                    # Create container for label and spinbox
                    container = QWidget()
                    container_layout = QHBoxLayout(container)
                    container_layout.setSpacing(10)
                    container_layout.setContentsMargins(5, 5, 5, 5)

                    # Create label
                    label_text = f"Output {i + 1}:"
                    label = QLabel(label_text)
                    label.setStyleSheet(label_style)
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                    # Create spinbox
                    spinbox = QSpinBox()
                    spinbox.setRange(1, 1000)
                    spinbox.setValue(i + 1)
                    spinbox.setStyleSheet(spinbox_style)
                    spinbox.setAlignment(Qt.AlignCenter)
                    spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

                    # Add to container
                    container_layout.addWidget(label)
                    container_layout.addWidget(spinbox)

                    # Add to column
                    column_layout.addWidget(container)

                    # Store reference
                    self.output_spinboxes.append((label, spinbox))

                # Add column to central container
                central_layout.addWidget(column_container)

            # Add the central container to the main layout
            self.outputs_layout.addWidget(central_container, 0, 0, alignment=Qt.AlignCenter)

        else:  # SINGLE SHOT or DOUBLE SHOT
            # For shot types, simple layout
            if is_double:  # DOUBLE SHOT
                # Create container to hold label and spinboxes
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setSpacing(10)
                container_layout.setContentsMargins(5, 5, 5, 5)

                # Create single label for both outputs
                label = QLabel("Outputs:")
                label.setStyleSheet(label_style)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                container_layout.addWidget(label)

                # Create spinbox container
                spinbox_container = QWidget()
                spinbox_layout = QHBoxLayout(spinbox_container)
                spinbox_layout.setSpacing(20)
                spinbox_layout.setContentsMargins(0, 0, 0, 0)

                # Create both spinboxes
                for i in range(2):
                    spinbox = QSpinBox()
                    spinbox.setRange(1, 1000)
                    spinbox.setValue(i + 1)
                    spinbox.setStyleSheet(spinbox_style)
                    spinbox.setAlignment(Qt.AlignCenter)
                    spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

                    # Add to spinbox container
                    spinbox_layout.addWidget(spinbox)

                    # Store reference (with the same label for both spinboxes)
                    self.output_spinboxes.append((label, spinbox))

                # Add spinbox container to main container
                container_layout.addWidget(spinbox_container)

                # Add to layout - centered
                self.outputs_layout.addWidget(container, 0, 0, alignment=Qt.AlignCenter)

            else:  # SINGLE SHOT
                # 1 centered
                # Create container for label and spinbox
                container = QWidget()
                container_layout = QHBoxLayout(container)
                container_layout.setSpacing(10)
                container_layout.setContentsMargins(5, 5, 5, 5)

                # Create label
                label = QLabel("Output:")
                label.setStyleSheet(label_style)
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # Create spinbox
                spinbox = QSpinBox()
                spinbox.setRange(1, 1000)
                spinbox.setValue(1)
                spinbox.setStyleSheet(spinbox_style)
                spinbox.setAlignment(Qt.AlignCenter)
                spinbox.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

                # Add to container
                container_layout.addWidget(label)
                container_layout.addWidget(spinbox)

                # Add to layout - centered
                self.outputs_layout.addWidget(container, 0, 0, alignment=Qt.AlignCenter)

                # Store reference
                self.output_spinboxes.append((label, spinbox))

        # Calculate dimensions for the middle container based on content
        if is_double and is_run:
            # For DOUBLE RUN
            row_height = 50  # Height per row
            min_height = max(150, min(4, (num_outputs // 2)) * row_height + 40)

            column_width = 400  # Width per column
            min_width = max(500, min(3, (num_outputs // 2 + 3) // 4) * column_width + 60)

        elif is_run:
            # For SINGLE RUN
            row_height = 50  # Height per row
            min_height = max(150, min(3, num_outputs) * row_height + 40)

            column_width = 200  # Width per column
            min_width = max(500, min(4, (num_outputs + 2) // 3) * column_width + 60)

        elif is_double:
            # For DOUBLE SHOT
            min_height = 150
            min_width = 500

        else:
            # For SINGLE SHOT
            min_height = 150
            min_width = 500

    def _set_next_available_cue_number(self):
        """Set the next available cue number based on existing cues"""
        if not self.existing_cues:
            return

        # Extract cue numbers from existing cues
        existing_numbers = []
        for cue in self.existing_cues:
            if isinstance(cue, list) and len(cue) > 0:
                existing_numbers.append(cue[0])
            elif isinstance(cue, dict) and "cue_number" in cue:
                existing_numbers.append(cue["cue_number"])

        if not existing_numbers:
            return

        # Find the next available number
        existing_numbers.sort()
        next_number = 1

        for num in existing_numbers:
            if num > next_number:
                break
            next_number = num + 1

        self.cue_number.setValue(next_number)

    def _collect_cue_data(self) -> dict:
        """Collect all cue data from form"""
        cue_type = self.cue_type.currentText()
        is_run = "RUN" in cue_type
        is_double = "DOUBLE" in cue_type

        cue_data = {
            "cue_number": self.cue_number.value(),
            "cue_type": cue_type,
            "execute_time": self.execute_time.value()
        }

        # Add run-specific data if applicable
        if is_run:
            cue_data["num_outputs"] = self.num_outputs.value()
            cue_data["delay"] = self.delay.value()

        # Collect actual output values from spinboxes
        output_values = []
        for _, spinbox in self.output_spinboxes:
            output_values.append(spinbox.value())
        cue_data["output_values"] = output_values

        # Format for table
        cue_data["formatted_for_table"] = self._format_for_table(cue_data)

        return cue_data

    def _format_for_table(self, cue_data):
        """Format the cue data for the table view"""
        cue_type = cue_data["cue_type"]
        is_run = "RUN" in cue_type
        is_double = "DOUBLE" in cue_type

        # Format outputs string based on cue type and output values
        outputs_str = ""
        output_values = cue_data.get("output_values", [])

        if is_run and is_double:  # DOUBLE RUN
            # Use commas for all outputs in DOUBLE RUN
            outputs_str = ", ".join(map(str, output_values))
        elif is_run:  # SINGLE RUN
            outputs_str = ", ".join(map(str, output_values))
        elif is_double:  # DOUBLE SHOT
            if len(output_values) >= 2:
                outputs_str = f"{output_values[0]}, {output_values[1]}"
            else:
                outputs_str = ", ".join(map(str, output_values))
        else:  # SINGLE SHOT
            if output_values:
                outputs_str = str(output_values[0])
            else:
                outputs_str = "1"  # Default

        # Format execute_time as 0:00.00 (minutes:seconds.milliseconds)
        execute_time = cue_data["execute_time"]
        formatted_time = execute_time

        try:
            # Handle different possible input formats
            if isinstance(execute_time, (int, float)) or (
                    isinstance(execute_time, str) and execute_time.replace('.', '', 1).isdigit()):
                # Convert to float to handle both int and float inputs
                total_seconds = float(execute_time)

                # Calculate minutes and seconds
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60

                # Format as 0:00.00
                formatted_time = f"{minutes}:{seconds:05.2f}"

            elif isinstance(execute_time, str) and ':' in execute_time:
                # Handle existing time format (could be various formats)
                parts = execute_time.split(':')

                if len(parts) == 3:  # HH:MM:SS format
                    hours, minutes, seconds = parts
                    # Convert to minutes:seconds format and add hours*60 to minutes
                    total_minutes = int(hours) * 60 + int(minutes)
                    formatted_time = f"{total_minutes}:{seconds}"

                    # Ensure seconds has 2 decimal places
                    if '.' not in formatted_time:
                        seconds_val = float(seconds)
                        formatted_time = f"{total_minutes}:{seconds_val:06.3f}"

                elif len(parts) == 2:  # MM:SS format
                    minutes, seconds = parts

                    # Ensure seconds has 2 decimal places
                    if '.' not in seconds:
                        seconds_val = float(seconds)
                        formatted_time = f"{minutes}:{seconds_val:05.2f}"
                    else:
                        # Make sure seconds is properly formatted with 2 decimal places
                        seconds_val = float(seconds)
                        formatted_time = f"{minutes}:{seconds_val:05.2f}"
        except Exception as e:
            print(f"Error formatting time: {e}")
            # Keep original if conversion fails

        # Create formatted list for table
        formatted_cue = [
            cue_data["cue_number"],
            cue_data["cue_type"],
            outputs_str,
            cue_data.get("delay", 0),
            formatted_time
        ]

        return formatted_cue

    def _validate_cue(self, cue_data: dict) -> bool:
        """Validate cue data before saving"""
        # Check for duplicate cue numbers
        cue_number = cue_data["cue_number"]
        for existing_cue in self.existing_cues:
            existing_number = None
            if isinstance(existing_cue, list) and len(existing_cue) > 0:
                existing_number = existing_cue[0]
            elif isinstance(existing_cue, dict) and "cue_number" in existing_cue:
                existing_number = existing_cue["cue_number"]

            if existing_number == cue_number:
                raise ValueError(f"Cue #{cue_number} already exists.")

        # Check for duplicate outputs - validate that each output is unique
        output_values = cue_data.get("output_values", [])
        if len(output_values) != len(set(output_values)):
            raise ValueError("Duplicate output values detected. Each output must be unique.")

        # Check if outputs are already in use by other cues
        used_outputs = set()
        for existing_cue in self.existing_cues:
            # Skip current cue if editing
            if isinstance(existing_cue, list) and len(existing_cue) > 0:
                if existing_cue[0] == cue_number:
                    continue

                # Parse outputs string from existing cues
                if len(existing_cue) > 2:
                    outputs_str = existing_cue[2]
                    # Handle different formats based on cue type
                    if "DOUBLE RUN" in existing_cue[1]:
                        # Format: "1,2; 3,4; 5,6"
                        pairs = outputs_str.split(";")
                        for pair in pairs:
                            for output in pair.strip().split(","):
                                try:
                                    used_outputs.add(int(output.strip()))
                                except ValueError:
                                    pass
                    else:
                        # Format: "1, 2, 3, 4"
                        for output in outputs_str.split(","):
                            try:
                                used_outputs.add(int(output.strip()))
                            except ValueError:
                                pass

        # Check for overlapping outputs
        for output in output_values:
            if output in used_outputs:
                raise ValueError(f"Output {output} is already used in another cue.")

        # Additional validation can be added here
        return True

    def _populate_fields_from_cue(self):
        """Populate all fields in the editor with data from the selected cue."""
        # Get the cue type for later use
        current_cue_type = ""
        if 'cue_type' in self.edit_cue and self.edit_cue['cue_type'] is not None:
            current_cue_type = self.edit_cue['cue_type']

        # Populate the cue number
        if 'cue_number' in self.edit_cue and self.edit_cue['cue_number'] is not None:
            try:
                # For QSpinBox, use setValue instead of setText
                cue_num = self.edit_cue['cue_number']
                # Convert to int if it's a string
                if isinstance(cue_num, str):
                    cue_num = int(cue_num)
                self.cue_number.setValue(cue_num)
            except (ValueError, TypeError) as e:
                print(f"Could not convert cue number to int: {self.edit_cue['cue_number']} - {str(e)}")

        # Populate the cue type if it exists
        if 'cue_type' in self.edit_cue and self.edit_cue['cue_type'] is not None:
            index = self.cue_type.findText(self.edit_cue['cue_type'])
            if index >= 0:
                self.cue_type.setCurrentIndex(index)

                # Update run fields with the selected cue type
                self._update_run_fields(current_cue_type)
        else:
            # If no cue type is specified, use the current selection
            current_cue_type = self.cue_type.currentText()
            self._update_run_fields(current_cue_type)

        # Populate delay if it exists
        if 'delay' in self.edit_cue and self.edit_cue['delay'] is not None:
            try:
                delay_value = self.edit_cue['delay']
                # Convert to float if it's a string
                if isinstance(delay_value, str):
                    delay_value = float(delay_value)
                self.delay.setValue(delay_value)
            except (ValueError, TypeError) as e:
                print(f"Could not convert delay value to float: {self.edit_cue['delay']} - {str(e)}")

        # Populate execute time if it exists
        if 'execute_time' in self.edit_cue and self.edit_cue['execute_time'] is not None:
            try:
                exec_time = self.edit_cue['execute_time']
                
                # Handle time in different formats
                if isinstance(exec_time, str):
                    # Check if it's in MM:SS.ss format
                    if ":" in exec_time:
                        parts = exec_time.split(":")
                        if len(parts) == 2:
                            minutes = float(parts[0])
                            seconds = float(parts[1])
                            exec_time = minutes * 60 + seconds
                    # Otherwise, try to convert directly to float
                    elif exec_time.strip() and exec_time.replace(".", "", 1).isdigit():
                        exec_time = float(exec_time)
                    else:
                        exec_time = 0
                        
                # Now set the value as a float
                self.execute_time.setValue(float(exec_time))
                
            except (ValueError, TypeError, AttributeError) as e:
                print(f"Could not set execute time: {self.edit_cue['execute_time']} - {str(e)}")
                # Default to 0 if there's an error
                self.execute_time.setValue(0)
    
        # Handle outputs - note: we don't call _update_output_spinboxes here as it will be called at the end of __init__
        if 'output_values' in self.edit_cue and self.edit_cue['output_values']:
            output_values = self.edit_cue['output_values']
    
            # Set number of outputs for RUN types
            if "RUN" in current_cue_type:
                self.num_outputs.setValue(len(output_values))
                
            # Store output values to be set after spinboxes are created
            self.edit_cue['_parsed_output_values'] = output_values
            
        elif 'outputs' in self.edit_cue and self.edit_cue['outputs']:
            # Try to parse outputs string
            try:
                output_str = str(self.edit_cue['outputs'])
                output_values = []
    
                # Handle different output formats (comma or semicolon separated)
                if ";" in output_str:
                    # Handle paired outputs
                    for pair in output_str.split(";"):
                        for value in pair.split(","):
                            if value.strip() and value.strip().replace(".", "", 1).isdigit():
                                output_values.append(float(value.strip()))
                else:
                    # Handle comma-separated outputs
                    for value in output_str.split(","):
                        if value.strip() and value.strip().replace(".", "", 1).isdigit():
                            output_values.append(float(value.strip()))
    
                if output_values:
                    # Set number of outputs for RUN types
                    if "RUN" in current_cue_type:
                        self.num_outputs.setValue(len(output_values))
                    
                    # Store output values to be set after spinboxes are created
                    self.edit_cue['_parsed_output_values'] = output_values
                    
            except Exception as e:
                print(f"Error parsing output values: {str(e)}")

    def keyPressEvent(self, event):
        """Handle keyboard events, particularly the Enter key to trigger the save button."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Call the same function that's connected to the save button
            self._validate_and_accept()
        else:
            # For other keys, use the default handling
            super().keyPressEvent(event)