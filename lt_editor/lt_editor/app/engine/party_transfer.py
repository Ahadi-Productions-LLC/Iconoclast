from app.constants import WINWIDTH, WINHEIGHT
from app.engine.sound import get_sound_thread
from app.engine.sprites import SPRITES
from app.engine.fonts import FONT
from app.engine.state import MapState, State
from app.engine.fluid_scroll import FluidScroll
from app.engine.input_manager import get_input_manager
from app.utilities import utils

from app.engine import menus, action, base_surf, engine, background, skill_system, text_funcs, image_mods
from app.engine.menus import Table
from app.engine.game_state import game
import logging, math


class PartyTransferTable(Table):
    
    # Overriding these such that you can scroll to ignored units.
    def move_to(self, idx):
        scroll = self.scroll
        idx = utils.clamp(idx, 0, len(self.options) - 1)
        #if self.options[idx].ignore:
        #    return
        self.current_index = idx
        row, col = self._true_coords(self.current_index)
        self.scroll = utils.clamp(self.scroll, row - self.rows + 1, row + self.rows - 1)
        # If we did scroll
        return scroll != self.scroll

    def move_down(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        row, col = self._true_coords(old_index)
        idx = old_index
        while True:
            if self.mode == 'objective_menu':
                row += 5
            else:
                row += 1
            if self._exists(row, col):
                pass
            elif first_push:
                row = 0
                self.scroll = 0
            else:
                # Set to most recent good option
                row = max(r for r in range(row) if self._exists(r, col) and not self.options[self._idx_coords(r, col)].ignore)
                idx = self._idx_coords(row, col)
                break
            idx = self._idx_coords(row, col)
            if row > self.scroll + self.rows - 5 and self.mode == 'objective_menu':
                self.scroll += 5
            elif row > self.scroll + self.rows - 2:
                self.scroll += 1
            elif row != 0:
                self.cursor.y_offset_down()
            #if not self.options[idx].ignore:
            #    break
            break
        self.current_index = idx
        if old_index == self.current_index:
            self.cursor.y_offset = 0
        num_rows = math.ceil(len(self.options) / self.columns)
        self.scroll = utils.clamp(self.scroll, 0, max(0, num_rows - self.rows))
        return old_index != self.current_index

    def move_up(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        row, col = self._true_coords(old_index)
        num_rows = math.ceil(len(self.options) / self.columns)
        idx = old_index
        while True:
            if self.mode == 'objective_menu':
                row -= 5
            else:
                row -= 1
            if self._exists(row, col):
                pass
            elif first_push:
                row = self._get_bottom(col)
                self.scroll = num_rows - self.rows
            else:
                # Set to most recent good option
                row = min(r for r in range(num_rows) if self._exists(r, col) and not self.options[self._idx_coords(r, col)].ignore)
                idx = self._idx_coords(row, col)
                break
            idx = self._idx_coords(row, col)
            if row < self.scroll + 4 and self.mode == 'objective_menu':
                self.scroll -= 5
            elif row < self.scroll + 1:
                self.scroll -= 1
            elif row != self._get_bottom(col):
                self.cursor.y_offset_up()
            #if not self.options[idx].ignore:
            #    break
            break
        self.current_index = idx
        self.scroll = max(0, self.scroll)
        if old_index == self.current_index:
            self.cursor.y_offset = 0
        return old_index != self.current_index

    def move_right(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        row, col = self._true_coords(old_index)
        idx = old_index
        num_rows = math.ceil(len(self.options) / self.columns)
        while True:
            col += 1
            if self._exists(row, col):
                pass
            elif idx >= len(self.options) - 1:
                break  # Don't move right because we are on the last row
            elif row < num_rows - 1:
                row += 1
                col = 0
                if row > self.scroll + self.rows - 2:
                    self.scroll += 1
                    self.scroll = utils.clamp(self.scroll, 0, max(0, num_rows - self.rows))
            else:
                # Set to most recent good option
                idx = max(i for i in range(len(self.options)) if not self.options[i].ignore)
                break
            idx = self._idx_coords(row, col)
            #if not self.options[idx].ignore:
            #    break
            break
        #if not self.options[idx].ignore:
        #    self.current_index = idx
        self.current_index = idx
        return old_index != self.current_index

    def move_left(self, first_push=True):
        if all(option.ignore for option in self.options):
            return
        old_index = self.current_index
        row, col = self._true_coords(old_index)
        idx = old_index
        while True:
            col -= 1
            if self._exists(row, col):
                pass
            elif row > 0:
                row -= 1
                col = self._get_right(row)
                if row < self.scroll + 1:
                    self.scroll -= 1
                    self.scroll = max(0, self.scroll)
            else:
                # Set to most recent good option
                idx = min(i for i in range(len(self.options)) if not self.options[i].ignore)
                break
            idx = self._idx_coords(row, col)
            #if not self.options[idx].ignore:
            #    break
            break
        #if not self.options[idx].ignore:
        #    self.current_index = idx
        self.current_index = idx
        return old_index != self.current_index

    # Setting a constant menu width for aesthetics.
    def get_menu_width(self):
        return 128

    def deactivate(self):
        self.active = False
        self.set_cursor(0)

    def activate(self):
        self.active = True
        self.set_cursor(1)

class PartyTransferState(State):
    name = 'party_transfer'

    def start(self):
        self.fluid = FluidScroll()
        self.bg = background.create_background('rune_background')
        self.top_party, self.bottom_party, self.fixed_list, self.top_party_name, self.bottom_party_name, \
            self.top_party_limit, self.bottom_party_limit = game.memory['party_transfer']
        self.top_units = [unit for unit in game.get_units_in_party(self.top_party.nid) if skill_system.can_select(unit)]
        self.bottom_units = [unit for unit in game.get_units_in_party(self.bottom_party.nid) if skill_system.can_select(unit)]        
        
        if not self.top_units:
            logging.error("party_transfer: no selectable units in party %s" % self.top_party)

        self.menu1 = PartyTransferTable(None, self.top_units, (4, 2), (2, 10))
        self.menu2 = PartyTransferTable(None, self.bottom_units, (4, 2), (2, 90), background='menu_bg_green')
        self.set_fixed()

        self.menu = self.menu1
        self.menu1.activate()
        self.menu2.deactivate()

        game.state.change('transition_in')
        return 'repeat'

    def take_input(self, event):
        first_push = self.fluid.update()
        directions = self.fluid.get_directions()
        
        self.handle_mouse()
        if 'DOWN' in directions:
            get_sound_thread().play_sfx('Select 5')
            row, col = self.menu._true_coords(self.menu.current_index)
            if self.menu1.active and row == self.menu._get_bottom(col) and len(self.bottom_units) > 0:
                self.menu2.activate()
                self.menu1.deactivate()
                self.menu = self.menu2
            else:
                self.menu.move_down(first_push)
        elif 'UP' in directions:
            get_sound_thread().play_sfx('Select 5')
            row, col = self.menu._true_coords(self.menu.current_index)
            if self.menu2.active and row == 0 and len(self.top_units) > 0:
                self.menu1.activate()
                self.menu2.deactivate()
                self.menu = self.menu1
            else:
                self.menu.move_up(first_push)
        elif 'LEFT' in directions:
            get_sound_thread().play_sfx('Select 5')
            self.menu.move_left(first_push)
        elif 'RIGHT' in directions:
            get_sound_thread().play_sfx('Select 5')
            self.menu.move_right(first_push)

        if event == 'SELECT':
            #if self.menu.current_index > len(self.menu.options):
            #    return
            unit = self.menu.get_current()
            if not unit:
                get_sound_thread().play_sfx('Select 4')
                return
            if unit.nid in self.fixed_list:
                get_sound_thread().play_sfx('Select 4')
            elif unit in self.top_units:
                self.top_units.remove(unit)
                self.bottom_units.append(unit)
                get_sound_thread().play_sfx('Select 1')
                self.update_options()
                if self.menu.current_index == len(self.menu.options):
                    self.menu.current_index = self.menu.current_index - 1
            elif unit in self.bottom_units:
                self.bottom_units.remove(unit)
                self.top_units.append(unit)
                get_sound_thread().play_sfx('Select 1')
                self.update_options()
                if self.menu.current_index == len(self.menu.options):
                    self.menu.current_index = self.menu.current_index - 1
            else:
                get_sound_thread().play_sfx('Error')
                return

        elif event == 'BACK':
            # No backing out of this menu
            get_sound_thread().play_sfx('Select 4')
            #game.state.change('transition_pop')

        elif event == 'INFO':
            get_sound_thread().play_sfx('Select 1')
            game.memory['scroll_units'] = game.get_units_in_party()
            game.memory['current_unit'] = self.menu.get_current()
            game.memory['next_state'] = 'info_menu'
            game.state.change('transition_to')

        elif event == 'START':
            if (self.bottom_party_limit and len(self.bottom_units) > self.bottom_party_limit) or \
               (self.top_party_limit and len(self.top_units) > self.top_party_limit):
                get_sound_thread().play_sfx('Error')
                return
            game.memory['party_transfer_sets'] = (self.top_units, self.bottom_units, self.top_party.nid, self.bottom_party.nid)
            game.state.change('party_transfer_confirm')
            get_sound_thread().play_sfx('Select 2')

    def update_options(self):
        self.menu1.create_options(self.top_units)
        self.menu2.create_options(self.bottom_units)
        self.set_fixed()

    def set_fixed(self):
        for idx in (self.menu1.options + self.menu2.options):
            if idx.get() and idx.unit.nid in self.fixed_list:
                idx.ignore = True

    def begin(self):
        # If come back from info menu
        unit = game.memory.get('current_unit')
        if unit and unit in self.top_units:
            idx = self.top_units.index(unit)
            self.menu1.move_to(idx)
        elif unit and unit in self.bottom_units:
            idx = self.bottom_units.index(unit)
            self.menu2.move_to(idx)
        game.memory['current_unit'] = None

    def draw(self, surf):
        if self.bg:
            self.bg.draw(surf)
        self.menu1.draw(surf)
        self.menu2.draw(surf)
        
        # Draw party names and limits
        FONT['text-blue'].blit(self.top_party_name, surf, (6, -2))
        FONT['text-blue'].blit(self.bottom_party_name, surf, (6, 77))

        if self.top_party_limit:
            top_party_full = [str(len(self.top_units)), '/', str(self.top_party_limit)]
            left_justify = 100
            if len(self.top_units) <= self.top_party_limit:
                top_font = ['text-blue', 'text-blue', 'text-blue']
            else:
                top_font = ['text-red', 'text-blue', 'text-blue']
            for word, font in zip(top_party_full, top_font):
                FONT[font].blit(word, surf, (left_justify, -2))
                left_justify += FONT[font].width(word)

        if self.bottom_party_limit:
            bottom_party_full = [str(len(self.bottom_units)), '/', str(self.bottom_party_limit)]
            left_justify = 100
            if len(self.bottom_units) <= self.bottom_party_limit:
                bottom_font = ['text-blue', 'text-blue', 'text-blue']
            else:
                bottom_font = ['text-red', 'text-blue', 'text-blue']
            for word, font in zip(bottom_party_full, bottom_font):
                FONT[font].blit(word, surf, (left_justify, 77))
                left_justify += FONT[font].width(word)

        # Draw button info
        sprite = SPRITES.get('buttons')
        buttons = [sprite.subsurface(0, 66, 14, 13), sprite.subsurface(0, 165, 33, 9)]
        font = FONT['text']
        commands = ['Swap', 'Done']
        commands = [text_funcs.translate(c) for c in commands]
        size = (49 + max(font.width(c) for c in commands), 40)
        button_surf = base_surf.create_base_surf(size[0], size[1], 'menu_bg_brown')
        button_surf = image_mods.make_translucent(button_surf, 0.1)
        button_surf.blit(buttons[0], (20 - buttons[0].get_width()//2, 18 - buttons[0].get_height()))
        button_surf.blit(buttons[1], (20 - buttons[1].get_width()//2, 32 - buttons[1].get_height()))
        for idx, command in enumerate(commands):
            font.blit(command, button_surf, (38, idx * 16 + 3))
        surf.blit(button_surf, (WINWIDTH//2 + 35, WINHEIGHT//2 + 25))
        
        # Draw info card
        menus.draw_unit_top(surf, (135,65), self.menu.get_current())
        
        return surf

    def handle_mouse(self) -> bool:
        mouse_position = get_input_manager().get_mouse_position()
        did_move = False
        if mouse_position:
            mouse_x, mouse_y = mouse_position
            idxs1, option_rects1 = self.menu1.get_rects()
            idxs2, option_rects2 = self.menu2.get_rects()
            # Menu1
            for idx, option_rect in zip(idxs1, option_rects1):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu1.mouse_move(idx)
                    did_move = True
                    if not self.menu1.active and len(self.top_units) > 0:
                        self.menu1.activate()
                        self.menu2.deactivate()
                        self.menu = self.menu1
                    self.menu.selecting_hand = (0, idx)
            # Menu2
            for idx, option_rect in zip(idxs2, option_rects2):
                x, y, width, height = option_rect
                if x <= mouse_x <= x + width and y <= mouse_y <= y + height:
                    self.menu2.mouse_move(idx)
                    did_move = True
                    if not self.menu2.active and len(self.bottom_units) > 0:
                        self.menu2.activate()
                        self.menu1.deactivate()
                        self.menu = self.menu2
                    self.menu.selecting_hand = (1, idx)
        return did_move

class PartyTransferConfirmState(MapState):
    name = 'party_transfer_confirm'
    transparent = True

    def start(self):
        self.header = 'Finish arranging parties?'
        options_list = ['Yes', 'No']
        self.orientation = 'vertical'
        self.menu = menus.Choice(None, options_list, 'center', None)
        self.bg_surf, self.topleft = self.create_bg_surf()
        self.menu.topleft = (self.topleft[0], self.topleft[1] + FONT['text'].height)

    def create_bg_surf(self):
        width_of_header = FONT['text'].width(self.header) + 16
        menu_width = self.menu.get_menu_width()
        width = max(width_of_header, menu_width)
        menu_height = self.menu.get_menu_height() if self.orientation == 'vertical' else FONT['text'].height + 8
        height = menu_height + FONT['text'].height
        bg_surf = base_surf.create_base_surf(width, height, 'menu_bg_base')
        topleft = (WINWIDTH//2 - width//2, WINHEIGHT//2 - height//2)
        return bg_surf, topleft

    def take_input(self, event):
        self.menu.handle_mouse()
        if (event == 'RIGHT' and self.orientation == 'horizontal') or \
                (event == 'DOWN' and self.orientation == 'vertical'):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_down()
        elif (event == 'LEFT' and self.orientation == 'horizontal') or \
                (event == 'UP' and self.orientation == 'vertical'):
            get_sound_thread().play_sfx('Select 6')
            self.menu.move_up()

        elif event == 'BACK':
            game.state.back()
            #get_sound_thread().play_sfx('Error')

        elif event == 'SELECT':
            get_sound_thread().play_sfx('Select 1')
            selection = self.menu.get_current()
            if selection == 'Yes':
                party1_units, party2_units, party1_nid, party2_nid = game.memory['party_transfer_sets']
                for unit in party1_units:
                    unit.party = party1_nid
                for unit in party2_units:
                    unit.party = party2_nid
                game.state.change('transition_double_pop')
            else:
                game.state.back()

    def draw(self, surf):
        surf.blit(self.bg_surf, self.topleft)
        FONT['text'].blit(self.header, surf, (self.topleft[0] + 4, self.topleft[1] + 4))

        # Place Menu on background
        self.menu.draw(surf)
        return surf
