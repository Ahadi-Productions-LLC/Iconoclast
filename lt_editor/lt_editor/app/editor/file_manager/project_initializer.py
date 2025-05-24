import shutil
from typing import Tuple

from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QFileDialog

from app.data.database.database import Database
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
from app.editor.new_game_dialog import NewGameDialog


class ProjectInitializer():
    def full_create_new_project(self):
        result = self.get_new_project_info()
        if result:
            nid, title, path = result
            self.initialize_new_project_files(nid, title, path)
            return nid, title, path
        return False

    def get_new_project_info(self) -> Tuple[str, str, str]:
        """Launches a few dialogs that query the user for required project info.

        Returns:
            Tuple[str, str, str]: (ID, Title, ProjectPath)
        """
        id_title_info = NewGameDialog.get()
        if not id_title_info:
            return False
        curr_path = QDir()
        curr_path.cdUp()
        proj_nid, proj_title = id_title_info
        starting_path = curr_path.path() + '/' + proj_title + '.ltproj'
        proj_path, ok = QFileDialog.getSaveFileName(None, "Save Project", starting_path,
                                                    "All Files (*)")
        if not ok:
            return False
        return proj_nid, proj_title, proj_path

    def initialize_new_project_files(self, nid, title, path):
        shutil.copytree(QDir.currentPath() + '/' + 'default.ltproj', path)
        new_project_db = Database()
        new_project_db.load(path, CURRENT_SERIALIZATION_VERSION)
        new_project_db.constants.get('game_nid').set_value(nid)
        new_project_db.constants.get('title').set_value(title)
        new_project_db.serialize(path)
