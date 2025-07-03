from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QStyleOptionHeader, QDialog, QWidget
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor, QDropEvent, QPainter
from views.dialogs.cue_editor_dialog import CueEditorDialog


class CueTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = []
        self._headers = [
            "CUE #",
            "TYPE",
            "# OF OUTPUTS",
            "OUTPUTS",
            "DELAY",
            "DURATION",
            "EXECUTE TIME"
        ]
        self._colors = {
            "SINGLE SHOT": QColor("#00FF00"),
            "DOUBLE SHOT": QColor("#FF0000"),
            "SINGLE RUN": QColor("#FFFF00"),
            "DOUBLE RUN": QColor("#FFA500")
        }

    def rowCount(self, parent=None):
        return 1000

    def columnCount(self, parent=None):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        col = index.column()

        if role == Qt.DisplayRole:
            if row < len(self._data):
                # CUE # (column 0)
                if col == 0:
                    return str(self._data[row][0])

                # TYPE (column 1)
                elif col == 1:
                    return str(self._data[row][1])

                # # OF OUTPUTS (column 2) - Calculated from OUTPUTS
                elif col == 2:
                    outputs = self._data[row][2]  # Get OUTPUTS column
                    try:
                        num_outputs = len(outputs.split(',')) if outputs else 0
                        return str(num_outputs)
                    except:
                        return "0"

                # OUTPUTS (column 3)
                elif col == 3:
                    return str(self._data[row][2])

                # DELAY (column 4)
                elif col == 4:
                    value = self._data[row][3]
                    if isinstance(value, (int, float)):
                        return f"{value:.2f}s"
                    return str(value)

                # DURATION (column 5) - Calculated from TYPE, OUTPUTS, and DELAY
                elif col == 5:
                    cue_type = self._data[row][1]  # Get TYPE
                    delay = self._data[row][3]  # Get DELAY
                    outputs = self._data[row][2]  # Get OUTPUTS

                    # For SHOT types, duration is 0
                    if "SHOT" in cue_type:
                        return "0.00s"
                    # For RUN types, calculate duration
                    else:
                        try:
                            num_outputs = len(outputs.split(',')) if outputs else 0
                            # Duration = (number of outputs - 1) * delay
                            duration = (num_outputs - 1) * float(delay)
                            return f"{duration:.2f}s"
                        except:
                            return "0.00s"

                # EXECUTE TIME (column 6)
                elif col == 6:
                    value = self._data[row][4]  # Get EXECUTE TIME
                    if '.' in value:
                        minutes, seconds = value.split(':')
                        return f"{minutes}:{seconds}"
                    else:
                        minutes, seconds = value.split(':')
                        return f"{minutes}:{seconds}.00"

                return str(self._data[row][col])
            return ""

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter

        elif role == Qt.BackgroundRole:
            if row % 2 == 0:
                return QColor("#1a1a2e")
            return QColor("#252540")

        elif role == Qt.ForegroundRole:
            if row < len(self._data):
                cue_type = self._data[row][1]  # Get TYPE
                return self._colors.get(cue_type, QColor("#FFFFFF"))
            return QColor("#FFFFFF")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            return str(section + 1)

    def flags(self, index):
        """Set flags to enable drag and drop"""
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def moveRow(self, sourceRow, destinationRow):
        """Move a row from source to destination position"""
        print(f"\nMoving row - Source: {sourceRow}, Destination: {destinationRow}")

        try:
            data_rows = len(self._data)
            print(f"Current data rows: {data_rows}")

            # Validate rows
            if sourceRow < 0 or sourceRow >= data_rows:
                print(f"Invalid source row: {sourceRow}")
                return False

            # Adjust destination if needed
            if destinationRow > data_rows:
                destinationRow = data_rows
                print(f"Adjusted destination to: {destinationRow}")

            if sourceRow == destinationRow:
                print("Source and destination are the same")
                return False

            # Perform the move
            self.beginMoveRows(QModelIndex(), sourceRow, sourceRow,
                               QModelIndex(), destinationRow)

            data = self._data.pop(sourceRow)
            if destinationRow > sourceRow:
                self._data.insert(destinationRow - 1, data)
            else:
                self._data.insert(destinationRow, data)

            self.endMoveRows()
            print("Move completed successfully")

            # Emit that the layout has changed
            self.layoutChanged.emit()
            return True

        except Exception as e:
            print(f"Error in moveRow: {str(e)}")
            return False

    def add_cue(self, cue_data):
        """Add a new cue to the model"""
        self._data.append(cue_data)
        self.layoutChanged.emit()  # Notify views of changes
        self.update_led_panel()

    def add_cues_batch(self, cue_data_list):
        """Add multiple cues efficiently with single UI update"""
        if not cue_data_list:
            return

        # Add all cues to data without triggering updates
        self._data.extend(cue_data_list)

        # Single UI update for all cues
        self.layoutChanged.emit()
        self.update_led_panel()

    def update_cue(self, index, cue_data):
        """Update an existing cue"""
        if 0 <= index < len(self._data):
            self._data[index] = cue_data
            self.layoutChanged.emit()
            self.update_led_panel()

    def remove_cue(self, cue_number):
        """Remove a cue by its number"""
        self._data = [cue for cue in self._data if cue[0] != cue_number]
        self.layoutChanged.emit()
        self.update_led_panel()

    def update_led_panel(self, force_refresh=False):
        """Update LED panel with current data

        Args:
            force_refresh: Force complete refresh of all LEDs (default: False)
        """
        if hasattr(self, 'led_panel'):
            self.led_panel.updateFromCueData(self._data, force_refresh=force_refresh)


class CueTableView(QTableView):
    def __init__(self):
        super().__init__()
        self.model = CueTableModel()
        self.setModel(self.model)
        self.setup_ui()

    def setup_ui(self):
        # Selection behavior
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)

        # Enhanced drag-drop configuration
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.InternalMove)
        self.setDropIndicatorShown(True)
        self.setDragDropOverwriteMode(False)
        self.setVerticalScrollMode(QTableView.ScrollPerPixel)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QTableView.DragDrop)

        # Additional drag-drop settings
        self.horizontalHeader().setDragEnabled(False)
        self.horizontalHeader().setAcceptDrops(False)
        self.verticalHeader().setDragEnabled(True)
        self.verticalHeader().setAcceptDrops(True)

        # Visual settings
        self.setShowGrid(True)
        self.setGridStyle(Qt.SolidLine)
        self.setCornerButtonEnabled(True)

        # Set column widths
        header = self.horizontalHeader()
        column_widths = [80, 120, 100, 200, 80, 80, 100]
        total_width = sum(column_widths)

        for col, width in enumerate(column_widths):
            header.setSectionResizeMode(col, QHeaderView.Fixed)
            self.setColumnWidth(col, width)

        # Set the table's fixed width to match columns exactly
        self.setFixedWidth(total_width + self.verticalHeader().width() +
                           self.verticalScrollBar().sizeHint().width())

        # Style the headers
        header_style = """
            QHeaderView::section {
                background-color: #1a1a2e;
                color: white;
                padding: 5px;
                border: 1px solid #333344;
            }
        """

        header.setStyleSheet(header_style)
        self.verticalHeader().setStyleSheet(header_style)

        # Main table styling with drag-drop visual feedback and corner button
        table_style = """
            QTableView {
                background-color: #1a1a2e;
                gridline-color: #333344;
                color: white;
                selection-background-color: #2d2d44;
                selection-color: white;
                border: none;
            }
            QTableView::item:selected {
                background-color: #2d2d44;
            }
            QTableView::item:focus {
                background-color: #3d3d54;
            }
            QTableView::drop-indicator {
                background-color: #4CAF50;
                border: 2px solid #45a049;
            }
            QTableCornerButton::section {
                background-color: #1a1a2e !important;
                border: 1px solid #333344 !important;
            }
        """

        self.setStyleSheet(table_style)

        # Force corner button styling with additional methods
        self.apply_corner_button_fix()

    def apply_corner_button_fix(self):
        """Apply comprehensive fix for the corner button styling"""
        try:
            # Enable corner button
            self.setCornerButtonEnabled(True)

            # Get corner button widget and apply direct styling
            corner_button = self.findChild(QWidget, "qt_scrollarea_cornerbutton")
            if corner_button:
                corner_button.setStyleSheet("""
                    QWidget {
                        background-color: #1a1a2e;
                        border: 1px solid #333344;
                    }
                """)

            # Alternative approach: find corner button by class name
            for child in self.findChildren(QWidget):
                if child.metaObject().className() == "QTableCornerButton":
                    child.setStyleSheet("""
                        QTableCornerButton {
                            background-color: #1a1a2e;
                            border: 1px solid #333344;
                        }
                    """)
                    break

        except Exception as e:
            print(f"Corner button fix error: {e}")

    def showEvent(self, event):
        """Override show event to apply corner button fix after widget is shown"""
        super().showEvent(event)
        # Apply corner button fix when widget becomes visible
        self.fix_corner_button_after_show()

    def fix_corner_button_after_show(self):
        """Apply corner button fix after the widget is fully shown"""
        try:
            # Force update of all child widgets
            self.update()

            # Try to find and style the corner button directly
            corner_button = None

            # Method 1: Find by object name
            corner_button = self.findChild(QWidget, "qt_scrollarea_cornerbutton")

            # Method 2: Find by iterating through children
            if not corner_button:
                for child in self.findChildren(QWidget):
                    if "corner" in child.objectName().lower() or child.metaObject().className() == "QTableCornerButton":
                        corner_button = child
                        break

            # Method 3: Direct corner button access
            if not corner_button:
                # Try to access corner button through table view internals
                if hasattr(self, 'cornerWidget'):
                    corner_button = self.cornerWidget()

            if corner_button:
                corner_button.setStyleSheet("""
                    * {
                        background-color: #1a1a2e !important;
                        border: 1px solid #333344 !important;
                    }
                """)
                print("Corner button found and styled successfully")
            else:
                print("Corner button not found - using alternative method")
                # Alternative: disable corner button completely
                self.setCornerButtonEnabled(False)

        except Exception as e:
            print(f"Corner button fix after show error: {e}")

    def resizeEvent(self, event):
        """Override resize event to maintain corner button styling"""
        super().resizeEvent(event)
        # Reapply corner button fix on resize
        try:
            self.fix_corner_button_after_show()
        except:
            pass

    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        print("Drag Enter Event")
        if event.source() == self:
            event.accept()
            print("Drag enter accepted")
        else:
            event.ignore()
            print("Drag enter ignored")

    def dragMoveEvent(self, event):
        """Handle drag move event"""
        print("Drag Move Event")
        try:
            if event.source() == self:
                drop_row = self.rowAt(event.pos().y())
                data_rows = len(self.model._data)
                print(f"Drag moving over row: {drop_row}, Data rows: {data_rows}")

                # Accept the drag even if beyond data rows
                event.accept()
                print("Drag move accepted")
            else:
                event.ignore()
                print("Drag move ignored")
        except Exception as e:
            print(f"Error in dragMoveEvent: {str(e)}")
            event.ignore()

    def dropEvent(self, event):
        """Handle drop event"""
        print("\nDrop Event Started")

        try:
            if event.source() != self:
                print("Drop ignored - wrong source")
                event.ignore()
                return

            # Get the row where the drop occurred
            drop_row = self.rowAt(event.pos().y())
            print(f"Initial drop position row: {drop_row}")

            # Get the source row (the one being dragged)
            source_row = -1
            for index in self.selectedIndexes():
                if index.column() == 0:  # Only need one index per row
                    source_row = index.row()
                    break

            print(f"Source row: {source_row}")

            if source_row == -1:
                print("No valid source row")
                event.ignore()
                return

            # Get the number of rows with actual data
            data_rows = len(self.model._data)
            print(f"Total rows with data: {data_rows}")

            # Adjust drop position if beyond data
            if drop_row >= data_rows:
                drop_row = data_rows
                print(f"Adjusted drop row to: {drop_row}")

            # Perform the move
            if self.model.moveRow(source_row, drop_row):
                print(f"Move successful: {source_row} -> {drop_row}")
                event.accept()

                # Select the moved row at its new position
                new_row = drop_row if drop_row < source_row else drop_row - 1
                self.selectRow(new_row)
                print(f"Selected row: {new_row}")
                return

            print("Move failed")
            event.ignore()

        except Exception as e:
            print(f"Error in dropEvent: {str(e)}")
            event.ignore()

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        print("\nMouse Press Event")
        index = self.indexAt(event.pos())
        if index.isValid():
            if self.selectionModel().isSelected(index):
                print("Deselecting row")
                self.selectionModel().clear()
                return
            print(f"Selected row: {index.row()}")
        super().mousePressEvent(event)

    def delete_selected_cue(self):
        """Delete the currently selected cue"""
        selection = self.selectionModel()
        if not selection.hasSelection():
            return False

        selected_rows = selection.selectedRows()
        if not selected_rows:
            return False

        row = selected_rows[0].row()
        if 0 <= row < len(self.model._data):
            # Get the cue number from the first column
            cue_number = self.model._data[row][0]

            # Remove the cue from the model
            self.model.remove_cue(cue_number)
            return True

        return False

    def delete_all_cues(self):
        """Delete all cues from the table"""
        if not self.model._data:
            return False

        # Clear the data
        self.model._data = []

        # Notify views of the change
        self.model.layoutChanged.emit()

        # Update LED panel
        self.model.update_led_panel(force_refresh=True)

        return True