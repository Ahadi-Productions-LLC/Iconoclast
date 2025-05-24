from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt

from app.utilities.data import Data
from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.database import item_components, skill_components

from app.editor.custom_widgets import WeaponTypeBox
from app.extensions.custom_gui import DeletionTab, DeletionDialog
from app.editor.base_database_gui import DragDropCollectionModel
from app.data.database.components import ComponentType, swap_values

import app.editor.utilities as editor_utilities

def get_pixmap(weapon):
    x, y = weapon.icon_index
    res = RESOURCES.icons16.get(weapon.icon_nid)
    if not res:
        return None
    if not res.pixmap:
        res.pixmap = QPixmap(res.full_path)
    pixmap = res.pixmap.copy(x*16, y*16, 16, 16)
    pixmap = QPixmap.fromImage(editor_utilities.convert_colorkey(pixmap.toImage()))
    return pixmap

class WeaponModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            weapon = self._data[index.row()]
            text = weapon.nid + " : " + weapon.name
            return text
        elif role == Qt.DecorationRole:
            weapon = self._data[index.row()]
            pixmap = get_pixmap(weapon)
            if pixmap:
                return QIcon(pixmap)
        return None

    def delete(self, idx):
        # Check to make sure nothing else is using me!!!
        weapon_type = self._data[idx]
        nid = weapon_type.nid
        affected_classes = [klass for klass in DB.classes if klass.wexp_gain.get(nid) and klass.wexp_gain.get(nid).wexp_gain > 0]
        affected_units = [unit for unit in DB.units if unit.wexp_gain.get(nid) and unit.wexp_gain.get(nid).wexp_gain > 0]
        affected_items = item_components.get_items_using(ComponentType.WeaponType, nid, DB)
        affected_skills = skill_components.get_skills_using(ComponentType.WeaponType, nid, DB)
        affected_weapons = [weapon for weapon in DB.weapons if weapon.advantage.contains(nid) or weapon.disadvantage.contains(nid)]
        
        deletion_tabs = []
        if affected_items:
            from app.editor.item_editor.item_model import ItemModel
            model = ItemModel
            msg = "Deleting WeaponType <b>%s</b> would affect these items." % nid
            deletion_tabs.append(DeletionTab(affected_items, model, msg, "Items"))
        if affected_skills:
            from app.editor.skill_editor.skill_model import SkillModel
            model = SkillModel
            msg = "Deleting WeaponType <b>%s</b> would affect these items." % nid
            deletion_tabs.append(DeletionTab(affected_skills, model, msg, "Skills"))
        if affected_classes:
            from app.editor.class_editor.class_model import ClassModel
            model = ClassModel
            msg = "Deleting WeaponType <b>%s</b> would affect these classes." % nid
            deletion_tabs.append(DeletionTab(affected_classes, model, msg, "Classes"))
        if affected_units:
            from app.editor.unit_editor.unit_model import UnitModel
            model = UnitModel
            msg = "Deleting WeaponType <b>%s</b> would affect these units." % nid
            deletion_tabs.append(DeletionTab(affected_units, model, msg, "Units"))
        if affected_weapons:
            model = WeaponModel
            msg = "Deleting WeaponType <b>%s</b> would affect these weapons." % nid
            deletion_tabs.append(DeletionTab(affected_weapons, model, msg, "Weapons"))
            
        if deletion_tabs:
            swap, ok = DeletionDialog.get_swap(deletion_tabs, WeaponTypeBox(self.window, exclude=weapon_type), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return  # User cancelled swap
        # Delete watchers
        # None needed
        super().delete(idx)

    def on_nid_changed(self, old_value, new_value):
        old_nid, new_nid = old_value, new_value
        for klass in DB.classes:
            if old_nid in klass.wexp_gain:
                if klass.wexp_gain.get(new_nid):
                    klass.wexp_gain[new_nid].wexp_gain += klass.wexp_gain[old_nid].wexp_gain
                    klass.wexp_gain[new_nid].usable = bool(klass.wexp_gain[new_nid].usable) or bool(klass.wexp_gain[old_nid].usable)
                else:
                    klass.wexp_gain[new_nid] = klass.wexp_gain[old_nid]
        for unit in DB.units:
            if old_nid in unit.wexp_gain:
                if unit.wexp_gain.get(new_nid):
                    unit.wexp_gain[new_nid].wexp_gain += unit.wexp_gain[old_nid].wexp_gain
                else:
                    unit.wexp_gain[new_nid] = unit.wexp_gain[old_nid]
        for weapon in DB.weapons:
            weapon.rank_bonus.swap_type(old_nid, new_nid)
            weapon.advantage.swap_type(old_nid, new_nid)
            weapon.disadvantage.swap_type(old_nid, new_nid)
        swap_values(DB.items.values(), ComponentType.WeaponType, old_nid, new_nid)
        swap_values(DB.skills.values(), ComponentType.WeaponType, old_nid, new_nid)

    def create_new(self):
        new_weapon = DB.weapons.create_new(DB)
        return new_weapon
