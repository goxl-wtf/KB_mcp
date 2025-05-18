import json
import uuid
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastmcp import FastMCP

# --- Configuration ---
# Store knowledge base data in a dedicated directory
KB_STORAGE_DIR = Path(__file__).parent / "knowledge_bases"
MCP_SERVER_NAME = "KnowledgeBaseManager"
CONTENT_PREVIEW_LENGTH = 500 # Maximum length for content previews

# --- State ---
# Variable to keep track of the currently selected knowledge base title
_selected_kb_title: Optional[str] = None

# Ensure the storage directory exists
KB_STORAGE_DIR.mkdir(exist_ok=True)

# --- Data Handling Helpers ---

def _get_kb_filepath(kb_title: str) -> Path:
    """Generates the filesystem path for a given knowledge base title."""
    # Simple sanitization for filename
    # Replace characters not allowed in filenames with underscores or remove them
    # This is a basic approach, more robust sanitization might be needed depending on OS/requirements
    sanitized_title = "".join(c for c in kb_title if c.isalnum() or c in (' ', '_', '-')).strip()
    if not sanitized_title: # Handle case where title becomes empty after sanitization
         sanitized_title = "untitled" # Fallback name
    filename = f"{sanitized_title}.json"
    return KB_STORAGE_DIR / filename

def _load_kb_data(kb_title: str) -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """Loads data for a specific knowledge base title."""
    filepath = _get_kb_filepath(kb_title)
    default_data = {"tasks": [], "notes": []}

    if not filepath.exists():
        # This function is called when a KB is expected to exist, so returning None indicates not found
        # However, in the context of the tool functions calling this after _check_selected_kb,
        # this path should ideally not be hit if _check_selected_kb passes.
        print(f"Warning: _load_kb_data called for non-existent KB '{kb_title}' at {filepath}")
        return None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Basic validation
            if not isinstance(data, dict) or "tasks" not in data or "notes" not in data:
                print(f"Warning: Knowledge base file {filepath} seems corrupt or has unexpected structure. Returning default structure.")
                return default_data
            return data
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}. Returning default structure.")
        return default_data
    except Exception as e:
        print(f"Error loading knowledge base '{kb_title}' from {filepath}: {e}")
        return default_data # Or maybe propagate exception depending on desired robustness

def _save_kb_data(kb_title: str, data: Dict[str, List[Dict[str, Any]]]):
    """Saves data for a specific knowledge base title."""
    filepath = _get_kb_filepath(kb_title)
    try:
        # Ensure directory exists before saving (redundant due to startup, but safe)
        filepath.parent.mkdir(exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving knowledge base '{kb_title}' to {filepath}: {e}")

# --- MCP Server Definition ---
mcp = FastMCP(MCP_SERVER_NAME)

# --- Knowledge Base Management Tools ---

@mcp.tool()
def list_knowledge_bases() -> List[str]:
    """
    Lists all available knowledge bases by their titles.
    """
    kb_titles = []
    try:
        if not KB_STORAGE_DIR.exists():
             return ["Error: Knowledge base storage directory not found."]
        for item in KB_STORAGE_DIR.iterdir():
            if item.is_file() and item.suffix == ".json":
                # Assume the title is the base name without the .json extension
                kb_titles.append(item.stem)
    except Exception as e:
        print(f"Error listing knowledge bases: {e}")
        return [f"Error: Could not list KBs due to filesystem error: {e}"]

    return sorted(kb_titles) if kb_titles else ["No knowledge bases found."]

@mcp.tool()
def create_knowledge_base(title: str) -> str:
    """
    Creates a new, empty knowledge base with the specified title.
    Returns a confirmation or an error if the title is invalid or already exists.
    """
    if not title or len(title.strip()) == 0:
        return "Error: Knowledge base title cannot be empty."

    filepath = _get_kb_filepath(title)

    if filepath.exists():
        return f"Error: Knowledge base '{title}' already exists."

    try:
        # Create the directory if it doesn't exist (redundant due to startup check, but safe)
        filepath.parent.mkdir(exist_ok=True)
        # Create the empty file with initial structure
        initial_data = {"tasks": [], "notes": []}
        with open(filepath, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return f"Knowledge base '{title}' created successfully."
    except Exception as e:
        print(f"Error creating knowledge base '{title}': {e}")
        return f"Error creating knowledge base '{title}': {e}"

@mcp.tool()
def select_knowledge_base(title: str) -> str:
    """
    Sets the active knowledge base for subsequent operations.
    Returns a confirmation or an error if the knowledge base is not found.
    """
    global _selected_kb_title # Declare intent to modify the global variable

    if not title or len(title.strip()) == 0:
         return "Error: Knowledge base title cannot be empty."

    filepath = _get_kb_filepath(title)

    if not filepath.exists():
        _selected_kb_title = None # Ensure state is clear if selection fails
        return f"Error: Knowledge base '{title}' not found."

    # Use the original title provided by the user for clarity in messages,
    # but ensure the file exists based on the sanitized version.
    # We could store the sanitized version if stricter internal consistency is needed.
    _selected_kb_title = title.strip()
    return f"Knowledge base '{_selected_kb_title}' selected."

@mcp.tool()
def rename_knowledge_base(old_title: str, new_title: str) -> str:
    """
    Renames an existing knowledge base.
    Returns a confirmation or an error if titles are invalid or conflict.
    """
    global _selected_kb_title # Declare intent to modify the global variable

    if not old_title or len(old_title.strip()) == 0:
        return "Error: Old title cannot be empty."
    if not new_title or len(new_title.strip()) == 0:
        return "Error: New title cannot be empty."

    old_filepath = _get_kb_filepath(old_title)
    new_filepath = _get_kb_filepath(new_title)

    if not old_filepath.exists():
        return f"Error: Knowledge base '{old_title}' not found."
    if new_filepath.exists():
        return f"Error: Knowledge base '{new_title}' already exists."
    if old_filepath == new_filepath:
         return f"Info: Knowledge base '{old_title}' is already effectively named '{new_title}' (sanitized filenames are the same)."

    try:
        os.rename(old_filepath, new_filepath)
        # If the renamed KB was currently selected, update the selected state
        if _selected_kb_title == old_title.strip():
            # Update selected title to the new one (using the potentially original new_title string)
            _selected_kb_title = new_title.strip()
            return f"Knowledge base '{old_title}' renamed to '{new_title}'. Selected KB updated to '{_selected_kb_title}'."
        else:
            return f"Knowledge base '{old_title}' renamed to '{new_title}'."
    except Exception as e:
        print(f"Error renaming knowledge base '{old_title}' to '{new_title}': {e}")
        return f"Error renaming knowledge base '{old_title}' to '{new_title}': {e}"


@mcp.tool()
def delete_knowledge_base(title: str, confirmation: str) -> str:
    """
    Deletes a knowledge base and its data permanently.
    Requires explicit confirmation by passing 'confirm' to the 'confirmation' parameter.
    Returns a confirmation or an error.
    """
    global _selected_kb_title # Declare intent to modify the global variable

    if not title or len(title.strip()) == 0:
         return "Error: Knowledge base title cannot be empty."
    if confirmation.lower() != 'confirm':
        return "Error: Action not confirmed. To delete the knowledge base, please provide 'confirm' as the confirmation argument."

    filepath = _get_kb_filepath(title)

    if not filepath.exists():
        return f"Error: Knowledge base '{title}' not found."

    try:
        os.remove(filepath)
        # If the deleted KB was currently selected, clear the selected state
        if _selected_kb_title == title.strip():
            _selected_kb_title = None
            return f"Knowledge base '{title}' deleted successfully. No knowledge base is currently selected."
        else:
            return f"Knowledge base '{title}' deleted successfully."
    except Exception as e:
        print(f"Error deleting knowledge base '{title}': {e}")
        return f"Error deleting knowledge base '{title}': {e}"


# --- Tools Operating on Selected Knowledge Base ---

def _check_selected_kb() -> Optional[str]:
    """Helper to check if a KB is selected and exists, returning an error message if not."""
    global _selected_kb_title # <-- Moved this to the top

    if _selected_kb_title is None:
        return "Error: No knowledge base selected. Please use `select_knowledge_base` first."

    filepath = _get_kb_filepath(_selected_kb_title)
    # Also check if the selected KB still exists on disk before proceeding
    if not filepath.exists():
         # This could happen if the file was deleted externally while it was selected
         _selected_kb_title = None # Clear the invalid state
         return f"Error: The previously selected knowledge base '{_selected_kb_title}' no longer exists. Please select a valid knowledge base."
    return None # No error, KB is selected and exists

@mcp.tool()
def view_scratchpad() -> Any: # Use Any as it can return Dict or str (error)
    """
    Retrieves the entire current content of the *selected* knowledge base,
    including all tasks (with completion status) and notes.
    Content of notes and descriptions of tasks are truncated if they exceed CONTENT_PREVIEW_LENGTH.
    Use get_full_note_content or get_full_task_description to retrieve full details.
    Returns error if no knowledge base is selected or found.
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}' after checking existence."

    processed_data = {"tasks": [], "notes": []}

    for task_data in data.get("tasks", []):
        description = task_data.get("description", "")
        if len(description) > CONTENT_PREVIEW_LENGTH:
            processed_data["tasks"].append({
                **task_data,
                "description_preview": description[:CONTENT_PREVIEW_LENGTH] + "...",
                "description_truncated": True,
                "description": None
            })
        else:
            processed_data["tasks"].append({
                **task_data,
                "description_preview": description,
                "description_truncated": False
            })

    for note_data in data.get("notes", []):
        content = note_data.get("content", "")
        if len(content) > CONTENT_PREVIEW_LENGTH:
            processed_data["notes"].append({
                **note_data,
                "content_preview": content[:CONTENT_PREVIEW_LENGTH] + "...",
                "content_truncated": True,
                "content": None
            })
        else:
            processed_data["notes"].append({
                **note_data,
                "content_preview": content,
                "content_truncated": False
            })

    return processed_data


@mcp.tool()
def add_task(description: str) -> str:
    """
    Adds a new task item to the *selected* knowledge base's task list.
    Generates a unique ID for the task.
    Returns a confirmation message with the new task's ID, or an error.
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if not description:
        return "Error: Task description cannot be empty."

    data = _load_kb_data(_selected_kb_title)
    if data is None: # Should be caught by _check_selected_kb, but defensive check
         return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."


    task_id = f"task_{uuid.uuid4().hex[:8]}"
    new_task = {"id": task_id, "description": description, "completed": False, "created_at": datetime.utcnow().isoformat() + "Z"}
    data["tasks"].append(new_task)
    _save_kb_data(_selected_kb_title, data)
    return f"Task added successfully to '{_selected_kb_title}' with ID: {task_id}"

@mcp.tool()
def complete_task(task_id: str) -> str:
    """
    Marks a specific task on the *selected* knowledge base as completed, using its unique ID.
    Returns a confirmation message or an error if the ID is not found or no KB is selected.
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if not task_id:
        return "Error: Task ID must be provided."

    data = _load_kb_data(_selected_kb_title)
    if data is None: # Defensive check
         return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    task_found = False
    for task in data["tasks"]:
        if task.get("id") == task_id:
            # Ensure the task object has the expected keys
            if not isinstance(task, dict):
                 continue # Skip if not a dictionary
            if task.get("completed", False): # Default to False if key missing
                return f"Task '{task_id}' in '{_selected_kb_title}' was already marked as completed."
            task["completed"] = True
            task["completed_at"] = datetime.utcnow().isoformat() + "Z"
            task_found = True
            break

    if task_found:
        _save_kb_data(_selected_kb_title, data)
        return f"Task '{task_id}' in '{_selected_kb_title}' marked as completed."
    else:
        return f"Error: Task with ID '{task_id}' not found in '{_selected_kb_title}'."


@mcp.tool()
def add_note(content: str) -> str:
    """
    Adds a piece of knowledge or a note to the *selected* knowledge base.
    Generates a unique ID for the note.
    Returns a confirmation message with the new note's ID, or an error.
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if not content:
        return "Error: Note content cannot be empty."

    data = _load_kb_data(_selected_kb_title)
    if data is None: # Defensive check
         return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    note_id = f"note_{uuid.uuid4().hex[:8]}"
    new_note = {"id": note_id, "content": content, "created_at": datetime.utcnow().isoformat() + "Z"}
    data["notes"].append(new_note)
    _save_kb_data(_selected_kb_title, data)
    return f"Note added successfully to '{_selected_kb_title}' with ID: {note_id}"

@mcp.tool()
def clear_scratchpad(confirmation: str) -> str:
    """
    Deletes ALL tasks and notes from the *selected* knowledge base.
    Requires explicit confirmation by passing 'confirm' to the 'confirmation' parameter.
    Returns a confirmation or an error if no KB is selected.
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if confirmation.lower() != 'confirm':
        return "Error: Action not confirmed. To clear the knowledge base, please provide 'confirm' as the confirmation argument."

    # Load data (even though we're just resetting it, this checks if the file exists and is accessible)
    data = _load_kb_data(_selected_kb_title)
    if data is None: # Defensive check, should be caught by _check_selected_kb
         return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}' before clearing."

    # Reset data to empty structure
    empty_data = {"tasks": [], "notes": []}
    _save_kb_data(_selected_kb_title, empty_data)
    return f"Knowledge base '{_selected_kb_title}' cleared successfully."

@mcp.tool()
def list_tasks(completed: Optional[bool] = None, search: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> Any:
    """List tasks in the selected knowledge base.

    Args:
        completed: Filter by completion state (True/False). If None, include all.
        search: Case-insensitive substring that must appear in the task description.
        limit: Max number of tasks to return.
        offset: Number of tasks to skip (for simple pagination).
    """
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    tasks_data = data.get("tasks", [])
    processed_tasks = []

    # Apply filters
    if completed is not None:
        tasks_data = [t for t in tasks_data if t.get("completed", False) == completed]
    if search:
        search_lower = search.lower()
        tasks_data = [t for t in tasks_data if search_lower in str(t.get("description", "")).lower()]

    # Sort by created_at if available (newest first)
    tasks_data.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    # Pagination
    if offset:
        tasks_data = tasks_data[offset:]
    if limit is not None:
        tasks_data = tasks_data[:limit]

    for task in tasks_data:
        description = task.get("description", "")
        if len(description) > CONTENT_PREVIEW_LENGTH:
            processed_tasks.append({
                **task,
                "description_preview": description[:CONTENT_PREVIEW_LENGTH] + "...",
                "description_truncated": True,
                "description": None # Or remove this key entirely
            })
        else:
            processed_tasks.append({
                **task,
                "description_preview": description, # Or use 'description' key directly
                "description_truncated": False
            })
    return processed_tasks


@mcp.tool()
def list_notes(search: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> Any:
    """List notes in the selected knowledge base with optional search & pagination."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    notes_data = data.get("notes", [])
    processed_notes = []

    if search:
        search_lower = search.lower()
        notes_data = [n for n in notes_data if search_lower in str(n.get("content", "")).lower()]

    # Sort by created_at (newest first)
    notes_data.sort(key=lambda n: n.get("created_at", ""), reverse=True)

    # Pagination
    if offset:
        notes_data = notes_data[offset:]
    if limit is not None:
        notes_data = notes_data[:limit]

    for note in notes_data:
        content = note.get("content", "")
        if len(content) > CONTENT_PREVIEW_LENGTH:
            processed_notes.append({
                **note,
                "content_preview": content[:CONTENT_PREVIEW_LENGTH] + "...",
                "content_truncated": True,
                "content": None # Or remove this key entirely
            })
        else:
            processed_notes.append({
                **note,
                "content_preview": content, # Or use 'content' key directly
                "content_truncated": False
            })
    return processed_notes


@mcp.tool()
def get_full_note_content(note_id: str) -> Any:
    """Retrieves the full content of a specific note by its ID."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if not note_id:
        return "Error: Note ID must be provided."

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    for note in data.get("notes", []):
        if note.get("id") == note_id:
            return note # Returns the full note, including its content
    
    return f"Error: Note with ID '{note_id}' not found in '{_selected_kb_title}'."

@mcp.tool()
def get_full_task_description(task_id: str) -> Any:
    """Retrieves the full description of a specific task by its ID."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    if not task_id:
        return "Error: Task ID must be provided."

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task # Returns the full task, including its description
    
    return f"Error: Task with ID '{task_id}' not found in '{_selected_kb_title}'."

@mcp.tool()
def uncomplete_task(task_id: str) -> str:
    """Marks a completed task as not completed (undo)."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            if not task.get("completed", False):
                return f"Task '{task_id}' is already uncompleted."
            task["completed"] = False
            task.pop("completed_at", None)
            _save_kb_data(_selected_kb_title, data)
            return f"Task '{task_id}' marked as not completed."

    return f"Error: Task with ID '{task_id}' not found in '{_selected_kb_title}'."


@mcp.tool()
def delete_task(task_id: str) -> str:
    """Deletes a task from the selected knowledge base."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    original_len = len(data.get("tasks", []))
    data["tasks"] = [t for t in data.get("tasks", []) if t.get("id") != task_id]

    if len(data["tasks"]) == original_len:
        return f"Error: Task with ID '{task_id}' not found in '{_selected_kb_title}'."

    _save_kb_data(_selected_kb_title, data)
    return f"Task '{task_id}' deleted from '{_selected_kb_title}'."


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Deletes a note from the selected knowledge base."""
    error_message = _check_selected_kb()
    if error_message:
        return error_message

    data = _load_kb_data(_selected_kb_title)
    if data is None:
        return f"Internal Error: Could not load data for selected KB '{_selected_kb_title}'."

    original_len = len(data.get("notes", []))
    data["notes"] = [n for n in data.get("notes", []) if n.get("id") != note_id]

    if len(data["notes"]) == original_len:
        return f"Error: Note with ID '{note_id}' not found in '{_selected_kb_title}'."

    _save_kb_data(_selected_kb_title, data)
    return f"Note '{note_id}' deleted from '{_selected_kb_title}'."

# --- Run the server (if executed directly) ---
# This part is mainly for direct testing, Claude Desktop uses the command/args
if __name__ == "__main__":
    import uvicorn
    import sys
    # FastMCP automatically sets up the app for uvicorn when run this way
    # Note: When run by Claude, MCP communication happens over stdio by default
    # unless configured for SSE. This __main__ block is for local dev testing.
    print(f"Starting {MCP_SERVER_NAME} server for local testing...", file=sys.stderr)
    print(f"Knowledge base storage directory: {KB_STORAGE_DIR}", file=sys.stderr)
    print("\nAvailable Tools:", file=sys.stderr)
    for tool_name in mcp.get_tool_list():
        print(f"- {tool_name}", file=sys.stderr)
    print("\nRemember to use `select_knowledge_base` first when using the tools!", file=sys.stderr)

    # Example of how you might start uvicorn for local testing:
    # uvicorn your_script_name:mcp.app --reload
    # (Assuming your script is named 'your_script_name.py')
    # You can test MCP communication directly with `mcp dev your_script_name.py`

    # Note: Running this __main__ block will not automatically select a KB for the MCP interface.
    # You would need to call the select_knowledge_base tool via the MCP interface.

    # If you wanted to select/create a default KB for local testing run via python directly, you could add:
    # default_kb = "default"
    # print(f"\nEnsuring default KB '{default_kb}' exists and selecting it for direct script execution...", file=sys.stderr)
    # create_knowledge_base(default_kb)
    # select_knowledge_base(default_kb)
    # print(f"Currently selected KB for direct execution: {_selected_kb_title}", file=sys.stderr)

    # Example usage if running directly (not via MCP):
    # print(add_task("Buy milk"))
    # print(add_note("Remember the meeting"))
    # print(view_scratchpad())