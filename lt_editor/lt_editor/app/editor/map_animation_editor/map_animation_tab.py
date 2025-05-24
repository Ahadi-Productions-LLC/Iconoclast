from app.data.resources.resources import RESOURCES

from app.extensions.custom_gui import ResourceListView
from app.editor.data_editor import SingleResourceEditor
from app.editor.base_database_gui import DatabaseTab

from app.editor.map_animation_editor import map_animation_model, map_animation_properties

class MapAnimationDatabase(DatabaseTab):
    @classmethod
    def create(cls, parent=None):
        data = RESOURCES.animations
        title = "Map Animation"
        right_frame = map_animation_properties.MapAnimationProperties
        collection_model = map_animation_model.MapAnimationModel
        deletion_criteria = None

        dialog = cls(data, title, right_frame, deletion_criteria,
                     collection_model, parent, button_text="Add New %s...",
                     view_type=ResourceListView)
        return dialog

    @classmethod
    def edit(cls, parent=None):
        window = SingleResourceEditor(MapAnimationDatabase, ['animations'], parent)
        window.exec_()

# Testing
# Run "python -m app.editor.map_animation_editor.map_animation_tab" from main directory
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION
    RESOURCES.load('default.ltproj', CURRENT_SERIALIZATION_VERSION)
    window = SingleResourceEditor(MapAnimationDatabase, ['animations'])
    window.show()
    app.exec_()
