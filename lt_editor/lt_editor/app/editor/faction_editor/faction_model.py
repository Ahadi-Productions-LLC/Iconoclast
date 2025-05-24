from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.data.resources.resources import RESOURCES

from app.utilities.data import Data
from app.data.database.database import DB

from app.extensions.custom_gui import DeletionTab, DeletionDialog

from app.editor.custom_widgets import FactionBox
from app.editor.base_database_gui import DragDropCollectionModel
import app.editor.utilities as editor_utilities
from app.utilities import str_utils

from app.data.database import factions

def get_pixmap(faction):
    x, y = faction.icon_index
    res = RESOURCES.icons32.get(faction.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x*32, y*32, 32, 32)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class FactionModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            faction = self._data[index.row()]
            text = faction.nid
            return text
        elif role == Qt.DecorationRole:
            faction = self._data[index.row()]
            pixmap = get_pixmap(faction)
            if pixmap:
                return QIcon(pixmap)
        return None

    def create_new(self):
        new_faction = DB.factions.create_new(DB)
        return new_faction

    def delete(self, idx):
        faction = self._data[idx]
        nid = faction.nid
        affected_ais = [ai for ai in DB.ai if ai.has_unit_spec("Faction", nid)]
        affected_levels = [level for level in DB.levels if any(unit.faction == nid for unit in level.units)]
        deletion_tabs = []
        if affected_ais:
            from app.editor.ai_editor.ai_model import AIModel
            model = AIModel
            msg = "Deleting Faction <b>%s</b> would affect these AIs" % nid
            deletion_tabs.append(DeletionTab(affected_ais, model, msg, "AIs"))
        if affected_levels:
            from app.editor.global_editor.level_menu import LevelModel
            model = LevelModel
            msg = "Deleting Faction <b>%s</b> would affect units in these levels" % nid
            deletion_tabs.append(DeletionTab(affected_levels, model, msg, "Levels"))

        if deletion_tabs:
            swap, ok = DeletionDialog.get_swap(deletion_tabs, FactionBox(self.window, exclude=faction), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        for ai in DB.ai:
            ai.change_unit_spec("Faction", old_nid, new_nid)
        for level in DB.levels:
            for unit in level.units:
                if unit.faction == old_nid:
                    unit.faction = new_nid
