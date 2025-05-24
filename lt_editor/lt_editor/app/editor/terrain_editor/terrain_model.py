from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import Qt

from app.data.database.database import DB
from app.data.resources.resources import RESOURCES

from app.extensions.custom_gui import DeletionTab, DeletionDialog

from app.editor.custom_widgets import TerrainBox
from app.editor.base_database_gui import DragDropCollectionModel

class TerrainModel(DragDropCollectionModel):
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            terrain = self._data[index.row()]
            text = terrain.nid + " : " + terrain.name
            return text
        elif role == Qt.DecorationRole:
            terrain = self._data[index.row()]
            color = terrain.color
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(color[0], color[1], color[2]))
            return QIcon(pixmap)
        return None

    def delete(self, idx):
        # Check to see what is using me?
        res = self._data[idx]
        nid = res.nid

        def check_tilemap(tilemap) -> bool:
            for layer in tilemap.layers:
                for key, terrain in layer.terrain_grid.items():
                    if terrain == nid:
                        return True
            return False

        def check_tileset(tileset) -> bool:
            for key, terrain in tileset.terrain_grid.items():
                if terrain == nid:
                    return True
            return False

        affected_tilemaps = [tilemap for tilemap in RESOURCES.tilemaps if check_tilemap(tilemap)]
        affected_tilesets = [tileset for tileset in RESOURCES.tilesets if check_tileset(tileset)]

        deletion_tabs = []
        if affected_tilemaps:
            from app.editor.tile_editor.tile_model import TileMapModel
            model = TileMapModel
            msg = "Deleting Terrain <b>%s</b> would affect these tilemaps." % nid
            deletion_tabs.append(DeletionTab(affected_tilemaps, model, msg, "Tilemaps"))
        if affected_tilesets:
            from app.editor.tile_editor.tile_model import TileSetModel
            model = TileSetModel
            msg = "Deleting Terrain <b>%s</b> would affect these tilesets." % nid
            deletion_tabs.append(DeletionTab(affected_tilesets, model, msg, "Tilesets"))

        if deletion_tabs:
            swap, ok = DeletionDialog.get_swap(deletion_tabs, TerrainBox(self.window, exclude=res), self.window)
            if ok:
                self.on_nid_changed(nid, swap.nid)
            else:
                return
        super().delete(idx)

    def on_nid_changed(self, old_nid, new_nid):
        for tilemap in RESOURCES.tilemaps:
            for layer in tilemap.layers:
                for coord, terrain in layer.terrain_grid.items():
                    if terrain == old_nid:
                        layer.terrain_grid[coord] = new_nid
        for tileset in RESOURCES.tilesets:
            for coord, terrain in tileset.terrain_grid.items():
                if terrain == old_nid:
                    tileset.terrain_grid[coord] = new_nid

    def create_new(self):
        new_terrain = DB.terrain.create_new(DB)
        return new_terrain
