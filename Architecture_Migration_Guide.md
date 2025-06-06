# Cue Management System Architecture Migration Guide

This guide provides practical steps for migrating the current code to the proposed 3-layer architecture.

## Current Architecture Issues

The existing codebase has several architectural challenges:

1. **Mixed Concerns**: UI code, data management, and application logic are intertwined
2. **Data Scattering**: Cue data is managed in multiple classes with no central model
3. **Tight Coupling**: Components are highly dependent on each other
4. **Limited Persistence**: Data is only stored in memory, not persisted between sessions

## Migration Plan

### Phase 1: Create the Models Layer

1. **Implement `models/cue_model.py`**

   Extract cue data management from existing files into a dedicated model:

   ```python
   # models/cue_model.py
   from typing import List, Dict, Callable, Any, Optional
   from dataclasses import dataclass

   @dataclass
   class Cue:
       cue_number: int
       cue_type: str
       outputs: str
       delay: float
       execute_time: str
       output_values: List[int] = None
       
       @property
       def is_run_type(self) -> bool:
           return "RUN" in self.cue_type
           
       @property
       def is_double_type(self) -> bool:
           return "DOUBLE" in self.cue_type
   
   class CueModel:
       def __init__(self):
           self._cues: List[Cue] = []
           self._observers: List[Callable] = []
           
       def add_cue(self, cue: Cue) -> bool:
           """Add a new cue to the model"""
           # Validate cue data
           if not self._is_valid_cue(cue):
               return False
               
           self._cues.append(cue)
           self._notify_observers()
           return True
           
       def update_cue(self, cue_number: int, updated_cue: Cue) -> bool:
           """Update an existing cue"""
           index = self._find_cue_index(cue_number)
           if index < 0:
               return False
               
           self._cues[index] = updated_cue
           self._notify_observers()
           return True
           
       def delete_cue(self, cue_number: int) -> bool:
           """Delete a cue by number"""
           index = self._find_cue_index(cue_number)
           if index < 0:
               return False
               
           del self._cues[index]
           self._notify_observers()
           return True
           
       def get_cues(self) -> List[Cue]:
           """Get all cues"""
           return self._cues.copy()
           
       def get_cue(self, cue_number: int) -> Optional[Cue]:
           """Get a specific cue by number"""
           index = self._find_cue_index(cue_number)
           if index < 0:
               return None
           return self._cues[index]
           
       def register_observer(self, callback: Callable) -> None:
           """Register observer to be notified of changes"""
           if callback not in self._observers:
               self._observers.append(callback)
               
       def unregister_observer(self, callback: Callable) -> None:
           """Remove observer"""
           if callback in self._observers:
               self._observers.remove(callback)
               
       def _notify_observers(self) -> None:
           """Notify all observers of changes"""
           for callback in self._observers:
               callback(self._cues)
               
       def _find_cue_index(self, cue_number: int) -> int:
           """Find index of cue with given number"""
           for i, cue in enumerate(self._cues):
               if cue.cue_number == cue_number:
                   return i
           return -1
           
       def _is_valid_cue(self, cue: Cue) -> bool:
           """Validate cue data"""
           # Check for duplicate cue numbers
           if self._find_cue_index(cue.cue_number) >= 0:
               return False
               
           # Check that output values are valid
           # Add other validation as needed
           return True
   ```

2. **Adapt existing code to use the model**:
   - Replace direct data access with model methods
   - Update code that modifies cues to use model methods

### Phase 2: Implement the Controller Layer

1. **Create `controllers/cue_controller.py`**

   ```python
   # controllers/cue_controller.py
   from typing import List, Dict, Any, Optional
   from CueManagementSystem.models.cue_model import CueModel, Cue

   class CueController:
       def __init__(self, model: CueModel):
           self.model = model
           
       def create_cue(self, cue_data: Dict[str, Any]) -> bool:
           """Process and validate cue creation"""
           # Convert dictionary to Cue object
           cue = self._dict_to_cue(cue_data)
           
           # Validate outputs
           if not self._validate_outputs(cue):
               return False
               
           # Add to model
           return self.model.add_cue(cue)
           
       def update_cue(self, cue_number: int, cue_data: Dict[str, Any]) -> bool:
           """Process and validate cue update"""
           # Convert dictionary to Cue object
           cue = self._dict_to_cue(cue_data)
           
           # Validate outputs
           if not self._validate_outputs(cue):
               return False
               
           # Update in model
           return self.model.update_cue(cue_number, cue)
           
       def delete_cue(self, cue_number: int) -> bool:
           """Delete a cue"""
           return self.model.delete_cue(cue_number)
           
       def select_cue(self, cue_number: int) -> Optional[Cue]:
           """Get a cue for selection"""
           return self.model.get_cue(cue_number)
           
       def _dict_to_cue(self, data: Dict[str, Any]) -> Cue:
           """Convert dictionary to Cue object"""
           # Handle different formats of input data
           # Format outputs string based on cue type
           return Cue(
               cue_number=data.get("cue_number", 0),
               cue_type=data.get("cue_type", ""),
               outputs=self._format_outputs(data),
               delay=data.get("delay", 0.0),
               execute_time=data.get("execute_time", "0:00.00"),
               output_values=data.get("output_values", [])
           )
           
       def _format_outputs(self, data: Dict[str, Any]) -> str:
           """Format outputs string based on cue type and values"""
           cue_type = data.get("cue_type", "")
           output_values = data.get("output_values", [])
           
           if not output_values:
               return ""
               
           if "DOUBLE RUN" in cue_type:
               # Format as pairs: "1,2; 3,4; 5,6"
               pairs = []
               for i in range(0, len(output_values), 2):
                   if i + 1 < len(output_values):
                       pairs.append(f"{output_values[i]},{output_values[i+1]}")
               return "; ".join(pairs)
           elif "RUN" in cue_type:
               # Format as comma list: "1, 2, 3, 4"
               return ", ".join(map(str, output_values))
           elif "DOUBLE" in cue_type:
               # Format as two values: "1, 2"
               if len(output_values) >= 2:
                   return f"{output_values[0]}, {output_values[1]}"
               return ", ".join(map(str, output_values))
           else:
               # Format as single value: "1"
               if output_values:
                   return str(output_values[0])
               return "1"
               
       def _validate_outputs(self, cue: Cue) -> bool:
           """Validate output values"""
           # Check for duplicate outputs
           if cue.output_values and len(cue.output_values) != len(set(cue.output_values)):
               return False
               
           # Check for conflicts with other cues' outputs
           all_cues = self.model.get_cues()
           used_outputs = set()
           
           for existing_cue in all_cues:
               # Skip the cue being validated
               if existing_cue.cue_number == cue.cue_number:
                   continue
                   
               # Collect outputs from existing cue
               if existing_cue.output_values:
                   used_outputs.update(existing_cue.output_values)
           
           # Check for conflicts
           if cue.output_values:
               for output in cue.output_values:
                   if output in used_outputs:
                       return False
                       
           return True
   ```

2. **Update view classes to use the controller**:
   - Replace direct model access with controller calls
   - Forward user actions to controller methods

### Phase 3: Database Integration

1. **Implement `models/database.py`**

   ```python
   # models/database.py
   import sqlite3
   from typing import List, Dict, Any, Optional
   import os
   from pathlib import Path
   from CueManagementSystem.models.cue_model import Cue

   class CueDatabase:
       def __init__(self, db_path: str = None):
           if db_path is None:
               # Default to a file in user's home directory
               home = str(Path.home())
               db_path = os.path.join(home, ".cue_management_system.db")
               
           self.db_path = db_path
           self.connection = self._create_connection()
           self._create_tables()
           
       def _create_connection(self) -> sqlite3.Connection:
           """Create a database connection"""
           try:
               conn = sqlite3.connect(self.db_path)
               # Enable foreign keys
               conn.execute("PRAGMA foreign_keys = ON")
               return conn
           except sqlite3.Error as e:
               print(f"Database connection error: {e}")
               raise
               
       def _create_tables(self) -> None:
           """Create necessary tables if they don't exist"""
           try:
               cursor = self.connection.cursor()
               
               # Create cues table
               cursor.execute('''
               CREATE TABLE IF NOT EXISTS cues (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   cue_number INTEGER NOT NULL UNIQUE,
                   cue_type TEXT NOT NULL,
                   outputs TEXT NOT NULL,
                   delay REAL DEFAULT 0,
                   execute_time TEXT NOT NULL,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
               )
               ''')
               
               # Create outputs table for normalized storage
               cursor.execute('''
               CREATE TABLE IF NOT EXISTS outputs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   cue_id INTEGER NOT NULL,
                   output_value INTEGER NOT NULL,
                   position INTEGER NOT NULL,
                   FOREIGN KEY (cue_id) REFERENCES cues(id) ON DELETE CASCADE,
                   UNIQUE(cue_id, output_value)
               )
               ''')
               
               self.connection.commit()
           except sqlite3.Error as e:
               print(f"Table creation error: {e}")
               raise
               
       def save_cue(self, cue: Cue) -> bool:
           """Save a cue to the database (insert or update)"""
           try:
               cursor = self.connection.cursor()
               
               # Check if cue already exists
               cursor.execute(
                   "SELECT id FROM cues WHERE cue_number = ?", 
                   (cue.cue_number,)
               )
               existing = cursor.fetchone()
               
               if existing:
                   # Update existing cue
                   cue_id = existing[0]
                   cursor.execute('''
                   UPDATE cues SET
                       cue_type = ?,
                       outputs = ?,
                       delay = ?,
                       execute_time = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?
                   ''', (
                       cue.cue_type,
                       cue.outputs,
                       cue.delay,
                       cue.execute_time,
                       cue_id
                   ))
                   
                   # Delete existing outputs for this cue
                   cursor.execute("DELETE FROM outputs WHERE cue_id = ?", (cue_id,))
               else:
                   # Insert new cue
                   cursor.execute('''
                   INSERT INTO cues (
                       cue_number, cue_type, outputs, delay, execute_time
                   ) VALUES (?, ?, ?, ?, ?)
                   ''', (
                       cue.cue_number,
                       cue.cue_type,
                       cue.outputs,
                       cue.delay,
                       cue.execute_time
                   ))
                   cue_id = cursor.lastrowid
               
               # Insert output values
               if cue.output_values:
                   for i, value in enumerate(cue.output_values):
                       cursor.execute('''
                       INSERT INTO outputs (cue_id, output_value, position)
                       VALUES (?, ?, ?)
                       ''', (cue_id, value, i))
               
               self.connection.commit()
               return True
           except sqlite3.Error as e:
               print(f"Save cue error: {e}")
               self.connection.rollback()
               return False
               
       def load_cues(self) -> List[Cue]:
           """Load all cues from the database"""
           try:
               cursor = self.connection.cursor()
               
               # Get all cues
               cursor.execute('''
               SELECT id, cue_number, cue_type, outputs, delay, execute_time
               FROM cues
               ORDER BY cue_number
               ''')
               
               cues = []
               for row in cursor.fetchall():
                   cue_id, cue_number, cue_type, outputs, delay, execute_time = row
                   
                   # Get output values for this cue
                   cursor.execute('''
                   SELECT output_value FROM outputs
                   WHERE cue_id = ?
                   ORDER BY position
                   ''', (cue_id,))
                   
                   output_values = [val[0] for val in cursor.fetchall()]
                   
                   cue = Cue(
                       cue_number=cue_number,
                       cue_type=cue_type,
                       outputs=outputs,
                       delay=delay,
                       execute_time=execute_time,
                       output_values=output_values
                   )
                   cues.append(cue)
               
               return cues
           except sqlite3.Error as e:
               print(f"Load cues error: {e}")
               return []
               
       def delete_cue(self, cue_number: int) -> bool:
           """Delete a cue from the database"""
           try:
               cursor = self.connection.cursor()
               cursor.execute(
                   "DELETE FROM cues WHERE cue_number = ?", 
                   (cue_number,)
               )
               self.connection.commit()
               return cursor.rowcount > 0
           except sqlite3.Error as e:
               print(f"Delete cue error: {e}")
               self.connection.rollback()
               return False
               
       def close(self) -> None:
           """Close the database connection"""
           if self.connection:
               self.connection.close()
   ```

2. **Update `models/cue_model.py` to use the database**:

   ```python
   # In CueModel class
   def __init__(self, database=None):
       self._cues: List[Cue] = []
       self._observers: List[Callable] = []
       self.database = database
       
       # Load cues from database if available
       if self.database:
           self._cues = self.database.load_cues()
           
   # Update methods to persist changes
   def add_cue(self, cue: Cue) -> bool:
       # Same validation logic...
       
       self._cues.append(cue)
       
       # Persist to database if available
       if self.database:
           self.database.save_cue(cue)
           
       self._notify_observers()
       return True
   
   # Similarly update update_cue and delete_cue methods
   ```

### Phase 4: Connect the Layers

1. **Update main application initialization**:

   ```python
   # In main.py or app initialization
   from CueManagementSystem.models.cue_model import CueModel
   from CueManagementSystem.models.database import CueDatabase
   from CueManagementSystem.controllers.cue_controller import CueController
   
   # Initialize layers
   database = CueDatabase()
   model = CueModel(database)
   controller = CueController(model)
   
   # Initialize main window with controller
   main_window = MainWindow(controller)
   ```

2. **Update MainWindow to use controller**:

   ```python
   # In MainWindow class
   def __init__(self, controller):
       super().__init__()
       self.controller = controller
       # Register as observer to model changes
       self.controller.model.register_observer(self.update_from_model)
       # Rest of initialization...
       
   def update_from_model(self, cues):
       """Update UI when model changes"""
       # Update table view
       # Update LED panel
       # etc.
       
   def handle_cue_validated(self, cue_data):
       """Handle validated cue data from creator"""
       success = self.controller.create_cue(cue_data)
       if not success:
           QMessageBox.critical(self, "Save Error", "Could not save cue")
           
   def handle_edited_cue(self, cue_data, original_cue_number):
       """Handle edited cue data from editor"""
       success = self.controller.update_cue(original_cue_number, cue_data)
       if not success:
           QMessageBox.critical(self, "Save Error", "Could not save edited cue")
   ```

## Benefits of This Migration

1. **Maintainability**: Clearly separated concerns make the code easier to understand and modify
2. **Testability**: Each layer can be tested independently
3. **Extensibility**: New features can be added without changing existing code
4. **Persistence**: Data is saved between sessions
5. **Reliability**: Better error handling and data validation
6. **Performance**: More efficient data access and processing

## Implementation Notes

- Implement one layer at a time and test thoroughly before moving to the next
- Keep compatibility with existing code during migration
- Create unit tests for each layer to ensure functionality
- Document API interfaces between layers
- Consider using dependency injection for better testability
