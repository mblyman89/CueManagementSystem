# models/database.py
import sqlite3
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from models.cue_model import Cue


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
                           CREATE TABLE IF NOT EXISTS cues
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               cue_number
                               INTEGER
                               NOT
                               NULL
                               UNIQUE,
                               cue_type
                               TEXT
                               NOT
                               NULL,
                               outputs
                               TEXT
                               NOT
                               NULL,
                               delay
                               REAL
                               DEFAULT
                               0,
                               execute_time
                               TEXT
                               NOT
                               NULL,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP,
                               updated_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            # Create outputs table for normalized storage
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS outputs
                           (
                               id
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               cue_id
                               INTEGER
                               NOT
                               NULL,
                               output_value
                               INTEGER
                               NOT
                               NULL,
                               position
                               INTEGER
                               NOT
                               NULL,
                               FOREIGN
                               KEY
                           (
                               cue_id
                           ) REFERENCES cues
                           (
                               id
                           ) ON DELETE CASCADE,
                               UNIQUE
                           (
                               cue_id,
                               output_value
                           )
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
                               UPDATE cues
                               SET cue_type     = ?,
                                   outputs      = ?,
                                   delay        = ?,
                                   execute_time = ?,
                                   updated_at   = CURRENT_TIMESTAMP
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
                               INSERT INTO cues (cue_number, cue_type, outputs, delay, execute_time)
                               VALUES (?, ?, ?, ?, ?)
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
                               SELECT output_value
                               FROM outputs
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