from PyQt5.QtWidgets import QItemDelegate
from PyQt5.QtCore import Qt

from app.utilities import str_utils
from app.data.database.database import DB

from app.extensions.custom_gui import ComboBox, PropertyBox, DeletionTab, DeletionDialog
from app.extensions.list_dialogs import MultiAttrListDialog
from app.extensions.list_models import MultiAttrListModel, DefaultMultiAttrListModel
from app.data.database.components import ComponentType, swap_values

from app.data.database.weapons import WeaponRank
from app.data.database import item_components, skill_components

class WeaponRankMultiModel(MultiAttrListModel):
    def delete(self, idx):
        # Check to make sure nothing else is using this rank
        element = DB.weapon_ranks[idx]
        affected_weapons = [weapon for weapon in DB.weapons if
                            any(adv.weapon_rank == element.rank for adv in weapon.rank_bonus) or
                            any(adv.weapon_rank == element.rank for adv in weapon.advantage) or
                            any(adv.weapon_rank == element.rank for adv in weapon.disadvantage)]
        affected_items = item_components.get_items_using(ComponentType.WeaponRank, element.rank, DB)
        affected_skills = skill_components.get_skills_using(ComponentType.WeaponRank, element.rank, DB)
        affected_classes = [klass for klass in DB.classes if 
                            any([wexp_gain.cap == element.requirement for wexp_gain in klass.wexp_gain.values()])]

        deletion_tabs = []
        if affected_weapons:
            from app.editor.weapon_editor.weapon_model import WeaponModel
            model = WeaponModel
            msg = "Deleting WeaponRank <b>%s</b> would affect these weapons." % element.rank
            deletion_tabs.append(DeletionTab(affected_weapons, model, msg, "Weapons"))
        if affected_items:
            from app.editor.item_editor.item_model import ItemModel
            model = ItemModel
            msg = "Deleting WeaponRank <b>%s</b> would affect these items." % element.rank
            deletion_tabs.append(DeletionTab(affected_items, model, msg, "Items"))
        if affected_items:
            from app.editor.skill_editor.skill_model import SkillModel
            model = SkillModel
            msg = "Deleting WeaponRank <b>%s</b> would affect these skills." % element.rank
            deletion_tabs.append(DeletionTab(affected_skills, model, msg, "Skills"))
        if affected_classes:
            from app.editor.class_editor.class_model import ClassModel
            model = ClassModel
            msg = "Deleting WeaponRank <b>%s</b> would modify these classes." % element.rank
            deletion_tabs.append(DeletionTab(affected_classes, model, msg, "Classes"))
        
        if deletion_tabs:
            combo_box = PropertyBox("Rank", ComboBox, self.window)
            objs = [rank for rank in DB.weapon_ranks if rank.rank != element.rank]
            combo_box.edit.addItems([rank.rank for rank in objs])
            obj_idx, ok = DeletionDialog.get_simple_swap(deletion_tabs, combo_box)
            
            if ok:
                swap = objs[obj_idx]
                for weapon in affected_weapons:
                    weapon.rank_bonus.swap_rank(element.rank, swap.rank)
                    weapon.advantage.swap_rank(element.rank, swap.rank)
                    weapon.disadvantage.swap_rank(element.rank, swap.rank)
                swap_values(DB.items.values(), ComponentType.WeaponRank, element.rank, swap.rank)
                swap_values(DB.skills.values(), ComponentType.WeaponRank, element.rank, swap.rank)
                for klass in affected_classes:
                    for weapon_type, wexp_gain in klass.wexp_gain.items():
                        if wexp_gain.cap == element.requirement:
                            wexp_gain.cap = swap.requirement
            else:
                return
        super().delete(idx)

    def create_new(self):
        nids = DB.weapon_ranks.keys()
        nid = str_utils.get_next_name("Rank", nids)
        new_weapon_rank = WeaponRank(nid, 1)
        DB.weapon_ranks.append(new_weapon_rank)
        return new_weapon_rank

    def on_attr_changed(self, data, attr, old_value, new_value):
        if attr == 'rank':
            self._data.update_nid(data, new_value)
            for weapon in DB.weapons:
                weapon.rank_bonus.swap_rank(old_value, new_value)
                weapon.advantage.swap_rank(old_value, new_value)
                weapon.disadvantage.swap_rank(old_value, new_value)
            swap_values(DB.items.values(), ComponentType.WeaponRank, old_value, new_value)
            swap_values(DB.skills.values(), ComponentType.WeaponRank, old_value, new_value)
        elif attr == 'requirement':
            for klass in DB.classes.values():
                for weapon_type, wexp_gain in klass.wexp_gain.items():
                    if wexp_gain.cap == old_value:
                        wexp_gain.cap = new_value

class RankDialog(MultiAttrListDialog):
    @classmethod
    def create(cls):
        def deletion_func(model, index):
            return model.rowCount() > 1

        return cls(DB.weapon_ranks, "Weapon Rank",
                   ("rank", "requirement"),
                   WeaponRankMultiModel, (deletion_func, None, None))

class WexpGainDelegate(QItemDelegate):
    bool_column = 0
    weapon_type_column = 1
    rank_columns = (2, 3)

    def createEditor(self, parent, option, index):
        if index.column() in self.rank_columns:
            editor = ComboBox(parent)
            editor.setEditable(True)
            editor.addItem('0')
            for rank in DB.weapon_ranks:
                editor.addItem(rank.rank)
            return editor
        else:
            return None

class WexpGainMultiAttrModel(DefaultMultiAttrListModel):
    def rowCount(self, parent=None):
        return len(DB.weapons)

    def data(self, index, role):
        if not index.isValid():
            return None
        if index.column() in self.checked_columns:
            if role == Qt.CheckStateRole:
                weapon_key = DB.weapons.keys()[index.row()]
                data = self._data.get(weapon_key, DB.weapons.default(DB))
                attr = self._headers[index.column()]
                val = getattr(data, attr)
                return Qt.Checked if bool(val) else Qt.Unchecked
            else:
                return None
        elif role == Qt.DisplayRole or role == Qt.EditRole:
            weapon_key = DB.weapons.keys()[index.row()]
            data = self._data.get(weapon_key, DB.weapons.default(DB))
            attr = self._headers[index.column()]
            if attr == 'nid':
                return weapon_key
            elif attr == 'cap':
                cap = getattr(data, attr)
                if cap is None:
                    return DB.weapon_ranks.get_highest_rank().requirement
                return cap
            else:
                return getattr(data, attr)
        return None

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        weapon_key = DB.weapons.keys()[index.row()]
        data = self._data.get(weapon_key)
        if not data:
            self._data[weapon_key] = DB.weapons.default(DB)
            data = self._data[weapon_key]
        attr = self._headers[index.column()]

        current_value = getattr(data, attr)
        if attr in ('wexp_gain', 'cap'):
            if value in DB.weapon_ranks:
                value = DB.weapon_ranks.get(value).requirement
            elif str_utils.is_int(value):
                value = int(value)
            else:
                value = 0
            setattr(data, attr, value)
            if attr == 'wexp_gain':
                usable = getattr(data, 'usable')
                if value > 0 and not usable:
                    self.on_attr_changed(data, 'usable', usable, True)
                    setattr(data, 'usable', True)
            self.on_attr_changed(data, attr, current_value, value)
            setattr(data, attr, value)
        elif attr == 'usable':
            self.on_attr_changed(data, 'usable', current_value, value)
            if value == Qt.Checked:
                setattr(data, 'usable', True)
            else:
                setattr(data, 'usable', False)
        self.dataChanged.emit(index, index)
        return True
