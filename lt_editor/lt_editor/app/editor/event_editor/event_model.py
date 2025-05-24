from PyQt5.QtCore import Qt

from app.data.database.database import DB

from app.editor.table_model import TableModel
from app.utilities import str_utils

class EventModel(TableModel):
    # rows = ['nid', 'level_nid', 'trigger']
    rows = ['name', 'level_nid', 'trigger']

    def headerData(self, idx, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Vertical:  # Row
            return '   '
        elif orientation == Qt.Horizontal:  # Column
            val = self.rows[idx]
            if val == 'nid':
                return 'ID'
            elif val == 'name':
                return 'Name'
            elif val == 'level_nid':
                return 'Level'
            else:
                return val.capitalize()
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            event = self._data[index.row()]
            str_attr = self.rows[index.column()]
            attr = getattr(event, str_attr)
            if str_attr == 'level_nid' and attr is None:
                return 'Global'
            return attr
        return None

    def create_new(self, level_nid=None):
        new_event = DB.events.create_new(DB, level_nid)
        return new_event

    def duplicate(self, index):
        if not index.isValid():
            return False
        idx = index.row()
        obj = self._data[idx]
        other_names = [o.name for o in self._data if o.level_nid == obj.level_nid]
        new_name = str_utils.get_next_name(obj.name, other_names)
        serialized_obj = obj.save()
        new_obj = self._data.datatype.restore(serialized_obj)
        new_obj.name = new_name
        self.layoutAboutToBeChanged.emit()
        self._data.insert(idx + 1, new_obj)
        self.layoutChanged.emit()
        new_index = self.index(idx + 1, 0)
        return new_index
