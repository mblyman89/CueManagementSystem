# Cue Management System Architecture

This document explains the proposed 3-layer architecture for the Cue Management System.

## 1. Models Layer (`models/cue_model.py`)

The Models Layer is responsible for data management and business logic. Moving cue data management to `models/cue_model.py` achieves:

- **Data Encapsulation**: All cue-related data structures and operations are defined in one place
- **Business Logic Isolation**: Validation rules, data transformations, and business rules are kept separate from UI
- **Reusability**: Data models can be reused across different views and controllers
- **Single Source of Truth**: All components access cue data through the model, avoiding inconsistencies

Current implementation has cue data scattered across multiple files (main_window.py, cue_table.py, etc.). Moving this to a dedicated model class creates a central place for managing all cue-related data.

Example model structure:
