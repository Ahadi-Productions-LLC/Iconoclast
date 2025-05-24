from PyQt5.QtCore import Qt

from app.data.database.database import DB

from app.editor.base_database_gui import DragDropCollectionModel

class DifficultyModeModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            difficulty_mode = self._data[index.row()]
            text = difficulty_mode.nid
            return text
        return None

    def create_new(self):
        new_difficulty_mode = DB.difficulty_modes.create_new(DB)
        return new_difficulty_mode

    def delete(self, idx):
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        pass
