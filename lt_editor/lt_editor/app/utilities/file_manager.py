from __future__ import annotations
import json
from pathlib import Path
import shutil

from app.utilities.typing import NestedPrimitiveDict

class FileManager():
    root: Path
    def __init__(self, root_dir: Path | str):
        self.root = Path(root_dir)

    def exists(self, relative_path_to_file: Path) -> bool:
        '''Check if a file exists

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs'''
        return (self.root / relative_path_to_file).exists()

    def get_path(self, relative_path_to_file: Path) -> Path:
        '''Get the full path to a file

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs'''
        return self.root / relative_path_to_file

    def load(self, relative_path_to_file: Path) -> str:
        '''Load a file from the file system

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs'''
        full_path = self.root / relative_path_to_file
        if not full_path.exists():
            raise FileNotFoundError(f"File {full_path} not found")
        return full_path.read_text()

    def load_json(self, relative_path_to_file: Path) -> NestedPrimitiveDict:
        '''Load a json file from the file system

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs'''
        return json.loads(self.load(relative_path_to_file))

    def save(self, relative_path_to_file: Path, content: str, overwrite: bool = False):
        '''Save a file to the file system

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs
            content (str): The content to write to the file
            overwrite (bool): Whether to overwrite the file if it already exists'''
        full_path = self.root / relative_path_to_file
        if full_path.exists() and not overwrite:
            raise FileExistsError(f"File {full_path} already exists")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    def copy(self, relative_path_to_file: Path, new_root: Path, overwrite: bool = False):
        '''Copy a file to a new location

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs
            new_root (Path): The new root directory to copy the file to
            overwrite (bool): Whether to overwrite the file if it already exists'''
        current_path = self.root / relative_path_to_file
        new_path = new_root / relative_path_to_file
        if not current_path.exists():
            raise FileNotFoundError(f"File {current_path} not found")
        if new_path.exists() and not overwrite:
            raise FileExistsError(f"File {new_path} already exists")
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(current_path, new_path)

    def copy_to(self, relative_path_to_file: Path, other_fman: FileManager, overwrite: bool = False):
        '''Copy a file to a new location

        Args:
            relative_path_to_file (Path): The relative path to the file within the game fs
            other_fman (FileManager): the file manager in charge of the new location
            overwrite (bool): Whether to overwrite the file if it already exists'''
        self.copy(relative_path_to_file, other_fman.root, overwrite)