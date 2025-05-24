from typing import Dict, List, Set

import os

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap

from app.utilities import str_utils
from app.utilities.typing import Color3
from app.data.resources.resources import RESOURCES
from app.data.resources import combat_anims, combat_commands, combat_palettes
from app.editor.combat_animation_editor.animation_import_utils import \
    convert_gba, split_doubles, combine_identical_commands, update_anim_full_image, \
    remove_top_right_palette_indicator, find_empty_pixmaps, stretch_vertically
from app.editor.combat_animation_editor.combat_effect_sound_table import SOUND_TABLE

from app.editor.settings import MainSettingsController
from app.editor.file_manager.project_file_backend import DEFAULT_PROJECT

import app.editor.utilities as editor_utilities

import logging

# Imports Spell Animations

# Object Frames:
# Object Frames are 480 x 160 pixels, the first 240x160 is the foreground in front of the battle animations
# the second 240x160 is drawn behind the battle animations

# Background Frames:
# 240x160 px, drawn in front of battle animations, but below object frame foreground

# Top right of Background frame image is background color, defaults to (0, 0, 0)

# CSA has a quirk where whenever certain command codes are processed, the object frame will not be displayed for that frame
# this quirk is not duplicated here

# CSA also has the quirk that no frame can be shown for only 1 frame. All 1 frame frames are automatically rendered as 2 frames
# This quick is not duplicated here

# Originally prototyped by MKCocoon and DecklynKern

def parse_spell_txt(fn: str, pixmaps: Dict[str, QPixmap], foreground_effect_name: str, background_effect_name: str,
                    empty_pixmaps: Set[str]):
    with open(fn) as fp:
        script_lines = [line.strip() for line in fp.readlines()]
        # Remove comment lines
        script_lines = [(line[:line.index('#')].strip() if '#' in line else line) for line in script_lines]
        script_lines = [line for line in script_lines if line]  # Remove empty lines

    stretch_foreground = False

    last_global_counter = 0  # Keeps track of what frame the last command to the main controller effect was added to
    current_counter = 0  # Keeps track of what frame the main controller effect should be on
    effect_start = None  # Keeps track of when the first frame is drawn
    has_panned = False
    current_blend: bool = False  # Keeps track of the current blend value for this effect so we don't duplicate commands
    current_partial_blend: int = 0  # Keeps track of the current partial blend value for this effect so we don't duplicate commands

    # This creates six lists of commands
    global_hit_commands = []
    global_miss_commands = []
    # For the object frames of the hit/attack pose
    hit_object_commands = []
    # For the background frames of the hit/attack pose
    hit_background_commands = []
    # For the object frames of the miss pose
    miss_object_commands = []
    # For the background frames of the miss pose
    miss_background_commands = []
    # Keeps track of what pixmaps are used for effect
    object_pixmaps = {}
    background_pixmaps = {}
    stretch_these_pixmaps = set()  # Ask the caller to stretch these pixmaps out (2x taller)

    most_recent_object_frame_command = None
    most_recent_background_frame_command = None

    def parse_text(command_text: str, hit_only: bool = False, miss_only: bool = False):
        nonlocal last_global_counter
        command = combat_commands.parse_text(command_text)
        # Add necessary waits to match up with the child effects
        if current_counter > last_global_counter:
            wait_command = combat_commands.parse_text(f'wait;{current_counter - last_global_counter}')
            global_hit_commands.append(wait_command)
            global_miss_commands.append(wait_command)

        if not miss_only:
            global_hit_commands.append(command)
        if not hit_only:
            global_miss_commands.append(command)
        last_global_counter = current_counter

    def add_wait(num_frames: int):
        parse_text(f'wait;{num_frames}')
        nonlocal last_global_counter, current_counter
        last_global_counter += num_frames  # Account for wait
        current_counter += num_frames  # Account for wait

    def duplicate_frame_commands(num_frames: int = 1):
        """
        This copies the most recent frame commands for both the object and background and places them again
        This is done because in CSA, whenever a C000000 type command is called, that takes a frame,
        which we will need to draw for that frame, since LT non-frame commands DON'T take actual time in engine
        """
        # Set the number of frames
        if most_recent_object_frame_command:
            object_command = most_recent_object_frame_command.__class__.copy(most_recent_object_frame_command)
            object_command.value = (num_frames, *object_command.value[1:])
            hit_object_commands.append(object_command)
            miss_object_commands.append(object_command)

        if most_recent_background_frame_command:
            background_command = most_recent_background_frame_command.__class__.copy(most_recent_background_frame_command)
            background_command.value = (num_frames, *background_command.value[1:])
            hit_background_commands.append(background_command)
            miss_background_commands.append(background_command)

    def process_command(line: str):
        if len(line) == 3:  # Shorthand commands
            arg1, arg2 = 0, 0
            command_code = line[1:]
        else:
            arg1 = int(line[1:3], 16)
            arg2 = int(line[3:5], 16)
            command_code = line[5:]

        # 00 through 13 (except 08) are ignored
        if command_code == '00':
            add_wait(1)
        elif command_code == '08':
            pass  # Attack (becomes critical automatically) with HP stealing
        # 14 through 28: passed to attacker's animation
        elif command_code == '14':
            parse_text('screen_shake')
            duplicate_frame_commands()
        elif command_code == '15':
            parse_text('platform_shake')
            duplicate_frame_commands()
        elif command_code == '1A':  # Start hit
            parse_text('enemy_flash_white;8', hit_only=True)
            add_wait(1)
            parse_text('screen_flash_white;4', hit_only=True)
            duplicate_frame_commands(2)
        elif command_code in ('1F', '20', '21'):  # spell hit or spell miss
            duplicate_frame_commands()
        elif command_code == '29':  # Set opacity and blending levels for background
            # handle opacity
            opacity = int(arg1 / 0x10 * 255)  # multiply by 255 to get into LT format
            opacity_command = combat_commands.parse_text(f'opacity;{opacity}')
            # add to ONLY the background
            hit_background_commands.append(opacity_command)
            miss_background_commands.append(opacity_command)

            # handle blend
            nonlocal current_blend, current_partial_blend
            should_blend = (arg2 > 0x00)  # 0x10 means full blending, 0x00 means no blending, anything over 0x00 is partial blending
            # Only bother if blend has changed
            if current_blend != should_blend:
                blend_command = combat_commands.parse_text('blend;1')
                blend_command.value = (should_blend,)
                current_blend = should_blend
                # add to ONLY the background
                hit_background_commands.append(blend_command)
                miss_background_commands.append(blend_command)
            # Partial blending section
            # When blending is not exactly 0 or 1, we have to duplicate the frame draw and draw once with blending set to true
            # and another with blending set to false, but have some opacity set to some in-between number.
            if 0x00 < arg2 < 0x10:
                value = int((arg2 / 0x10) * 255)
            else:
                value = 0
            if current_partial_blend != value:
                partial_blend_command = combat_commands.get_command('partial_blend')
                partial_blend_command.value = (value, )
                # add to ONLY the background
                hit_background_commands.append(partial_blend_command)
                miss_background_commands.append(partial_blend_command)

            duplicate_frame_commands()
        elif command_code == '2A':  # Whether maps 2 and 3 of the GBA screen should be visible
            # display_maps = (arg2 != 0)
            pass
        # 2B through 3F: passed to attacker's animation
        elif command_code == '40':  # Scrolls screen from being centered on the attacker to being centered on the defender
            parse_text("pan")
            nonlocal has_panned
            has_panned = True
        # 41 through 47: passed to attacker's animation
        elif command_code == '48':  # Plays sound or music whose ID corresponds to those documented in Music List.txt of the nightmare module packages
            sound_id = arg1 * 256 + arg2
            try:
                sound_name = SOUND_TABLE[sound_id]
                parse_text(f"sound;{sound_name}")
            except KeyError as e:
                logging.error(f"Unable to determine sound with id: {sound_id}")
                logging.exception(e)
            duplicate_frame_commands()
        # 49 through 51: passed to attacker's animation
        elif command_code == '53':  # Enable screen stretch
            nonlocal stretch_foreground
            stretch_foreground = bool(arg2)

    # At the beginning, set the background effect to use blending
    # hit_background_commands.append(combat_commands.parse_text('blend;1'))
    # miss_background_commands.append(combat_commands.parse_text('blend;1'))

    # At the beginning, darken
    parse_text('darken')
    add_wait(4)

    for idx, line in enumerate(script_lines):
        logging.info(f"Processing script line: {line}")

        if line.startswith('/// - '):
            pass

        elif line.startswith('C'):
            process_command(line)

        elif line.startswith('O'):
            if effect_start is None:
                effect_start = current_counter
                parse_text(f"effect;{foreground_effect_name}")
                parse_text(f"under_effect;{background_effect_name}")

            object_image_fn = line.split()[-1]
            object_image_name = object_image_fn[:-4]  # Remove .png
            background_image_fn = script_lines[idx + 1].split()[-1]
            background_image_name = background_image_fn[:-4] # Remove .png
            num_frames = int(script_lines[idx + 2])

            if object_image_name not in pixmaps:
                logging.error(f"{object_image_name} not in pixmaps")
                raise ValueError(f"{object_image_name} not in pixmaps")
            under_object_image_name = object_image_name + '_under'
            if under_object_image_name not in pixmaps:
                logging.error(f"{under_object_image_name} not in pixmaps")
                raise ValueError(f"{under_object_image_name} not in pixmaps")
            if object_image_name in empty_pixmaps and under_object_image_name in empty_pixmaps:  # Do nothing
                object_frame_command = combat_commands.parse_text(f'wait;{num_frames}')
            elif object_image_name in empty_pixmaps:  # Only display the under
                object_frame_command = combat_commands.parse_text(f'uf;{num_frames};{under_object_image_name}')
                object_pixmaps[under_object_image_name] = pixmaps[under_object_image_name]
            elif under_object_image_name in empty_pixmaps:  # Only display the main frame
                object_frame_command = combat_commands.parse_text(f'f;{num_frames};{object_image_name}')
                object_pixmaps[object_image_name] = pixmaps[object_image_name]
            else:  # Display both frames
                object_frame_command = combat_commands.parse_text(f'f;{num_frames};{object_image_name};{under_object_image_name}')
                object_pixmaps[object_image_name] = pixmaps[object_image_name]
                object_pixmaps[under_object_image_name] = pixmaps[under_object_image_name]

            if background_image_name not in pixmaps:
                logging.error(f"{background_image_name} not in pixmaps")
                raise ValueError(f"{background_image_name} not in pixmaps")
            if background_image_name in empty_pixmaps:
                background_frame_command = combat_commands.parse_text(f'wait;{num_frames}')
            else:
                background_frame_command = combat_commands.parse_text(f'f;{num_frames};{background_image_name}')
                background_pixmaps[background_image_name] = pixmaps[background_image_name]

            for im_name in (object_image_name, under_object_image_name, background_image_name):
                if stretch_foreground and im_name not in empty_pixmaps:
                    if pixmaps[im_name].height() <= 120:
                        stretch_these_pixmaps.add(im_name)
                    else:  # Automatically crop the one's that are too big...
                        pix = pixmaps[im_name]
                        new_pix = pix.copy(0, 0, pix.width(), 80)
                        pixmaps[im_name] = new_pix
                        stretch_these_pixmaps.add(im_name)

            hit_object_commands.append(object_frame_command)
            miss_object_commands.append(object_frame_command)

            hit_background_commands.append(background_frame_command)
            miss_background_commands.append(background_frame_command)

            most_recent_object_frame_command = object_frame_command
            most_recent_background_frame_command = background_frame_command

            current_counter += num_frames

        elif line.startswith('~'):  # Miss terminator
            parse_text('spell_hit', hit_only=True)
            parse_text('miss', miss_only=True)

    # At the end of the parse, break out of the spell
    if has_panned:  # pan back
        parse_text('pan')
        add_wait(4)
    # Cleanup
    parse_text('end_parent_loop')
    parse_text('lighten')
    add_wait(8)

    return global_hit_commands, global_miss_commands, \
        hit_object_commands, miss_object_commands, \
        hit_background_commands, miss_background_commands, \
        object_pixmaps, background_pixmaps, stretch_these_pixmaps


def import_effect_from_gba(fn: str, effect_name: str):
    """
    Imports spell animations from a properly formatted GBA CSA script file
    and creates a new spell effect animation

    Parameters
    ----------
    fn: str, filename
        "*.txt" file to read from
    effect_name: str
        What the nid of the new effect should be
    """
    directory = os.path.split(os.path.abspath(fn))[0] 
    logging.info(f"Import GBA weapon animation from script {fn} in {directory}")

    foreground_effect_name = str_utils.get_next_name(effect_name + '_fg', RESOURCES.combat_effects.keys())
    background_effect_name = str_utils.get_next_name(effect_name + '_bg', RESOURCES.combat_effects.keys())

    images = []
    for image_fn in os.listdir(directory):
        if image_fn.endswith('.png'):
            images.append(os.path.join(directory, image_fn))
    logging.info("Images located: %s", images)
    if not images:
        QMessageBox.critical(None, "Error", "Cannot find valid images in %s!" % directory)
        return

    # Convert to pixmaps
    pixmaps = {os.path.split(path)[-1][:-4]: QPixmap(path) for path in images}
    # Convert to GBA colors
    pixmaps = {name: convert_gba(pix) for name, pix in pixmaps.items()}
    # Split double images into "_under" image
    pixmaps = split_doubles(pixmaps)
    # Remove top right palette indicator
    pixmaps = remove_top_right_palette_indicator(pixmaps)
    # Determine which pixmaps should be replaced by "wait" commands
    empty_pixmaps: Set[str] = find_empty_pixmaps(pixmaps, exclude_color=editor_utilities.qEFFECT_COLORKEY)
    print(f"{empty_pixmaps=}")

    global_hit, global_miss, hit_foreground_effect, miss_foreground_effect, \
        hit_background_effect, miss_background_effect, \
        object_pixmaps, background_pixmaps, stretch_these_pixmaps = \
        parse_spell_txt(fn, pixmaps, foreground_effect_name, background_effect_name, empty_pixmaps)

    # Any pixmap which needs stretching, do it now
    for pixmap_name in stretch_these_pixmaps:
        pix = pixmaps[pixmap_name]
        pix = stretch_vertically(pix)
        pixmaps[pixmap_name] = pix
        if pixmap_name in object_pixmaps:
            object_pixmaps[pixmap_name] = pix
        if pixmap_name in background_pixmaps:
            background_pixmaps[pixmap_name] = pix

    # Posify
    # Global Controller
    hit_pose = combat_anims.Pose("Attack")
    for command in global_hit:
        hit_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(hit_pose)
    miss_pose = combat_anims.Pose("Miss")
    for command in global_miss:
        miss_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(miss_pose)

    controller_effect = combat_anims.EffectAnimation(effect_name)
    controller_effect.poses.append(hit_pose)
    controller_effect.poses.append(miss_pose)

    # Foreground Effect
    hit_pose = combat_anims.Pose("Attack")
    for command in hit_foreground_effect:
        hit_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(hit_pose)
    miss_pose = combat_anims.Pose("Miss")
    for command in miss_foreground_effect:
        miss_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(miss_pose)

    foreground_effect = combat_anims.EffectAnimation(foreground_effect_name)
    foreground_effect.poses.append(hit_pose)
    foreground_effect.poses.append(miss_pose)

    # Background Effect
    hit_pose = combat_anims.Pose("Attack")
    for command in hit_background_effect:
        hit_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(hit_pose)
    miss_pose = combat_anims.Pose("Miss")
    for command in miss_background_effect:
        miss_pose.timeline.append(command.__class__.copy(command))
    combine_identical_commands(miss_pose)

    background_effect = combat_anims.EffectAnimation(background_effect_name)
    background_effect.poses.append(hit_pose)
    background_effect.poses.append(miss_pose)

    # === PALETTES ===
    def assign_palette(pixmaps, effect_anim, name):
        # Find palettes for effect pixmaps
        all_palette_colors: List[Color3] = editor_utilities.find_palette_from_multiple([pix.toImage() for pix in pixmaps.values()])
        EFFECT_BG_COLOR = (0, 0, 0)
        if EFFECT_BG_COLOR != all_palette_colors[0]:
            if EFFECT_BG_COLOR in all_palette_colors:
                all_palette_colors.remove(EFFECT_BG_COLOR)
            all_palette_colors.insert(0, EFFECT_BG_COLOR)

        print("assign palette", name, all_palette_colors)
        # Always generate a new palette
        palette_nid = str_utils.get_next_name("New Palette", RESOURCES.combat_palettes.keys())
        palette = combat_palettes.Palette(palette_nid)
        RESOURCES.combat_palettes.append(palette)
        palette_name = str_utils.get_next_name(name, [name for name, nid in foreground_effect.palettes])
        effect_anim.palettes.append([palette_name, palette.nid])
        palette.assign_colors(all_palette_colors)
        return palette

    # Convert pixmaps to new palette colors
    if object_pixmaps:
        effect_palette = assign_palette(object_pixmaps, foreground_effect, "FG Effect")
        effect_convert_dict = editor_utilities.get_color_conversion(effect_palette)
        object_pixmaps = {name: editor_utilities.color_convert_pixmap(pix, effect_convert_dict) for name, pix in object_pixmaps.items()}

    if background_pixmaps:
        under_effect_palette = assign_palette(background_pixmaps, background_effect, "BG Effect")
        under_effect_convert_dict = editor_utilities.get_color_conversion(under_effect_palette)
        background_pixmaps = {name: editor_utilities.color_convert_pixmap(pix, under_effect_convert_dict) for name, pix in background_pixmaps.items()}

    # Actually put the pixmaps into the effect animations
    print("Object Pixmaps")
    for name, pix in object_pixmaps.items():
        x, y, width, height = editor_utilities.get_bbox(pix.toImage(), exclude_color=editor_utilities.qEFFECT_COLORKEY)
        pix = pix.copy(x, y, width, height)
        print(name, x, y, width, height)
        frame = combat_anims.Frame(name, (0, 0, width, height), (x, y), pixmap=pix)
        foreground_effect.frames.append(frame)
    print("Background Pixmaps")
    for name, pix in background_pixmaps.items():
        x, y, width, height = editor_utilities.get_bbox(pix.toImage(), exclude_color=editor_utilities.qEFFECT_COLORKEY)
        pix = pix.copy(x, y, width, height)
        print(name, x, y, width, height)
        frame = combat_anims.Frame(name, (0, 0, width, height), (x, y), pixmap=pix)
        background_effect.frames.append(frame)

    # Now collate the frames
    update_anim_full_image(foreground_effect)
    update_anim_full_image(background_effect)

    # Now add to list of all effects!
    RESOURCES.combat_effects.append(controller_effect)
    RESOURCES.combat_effects.append(foreground_effect)
    RESOURCES.combat_effects.append(background_effect)

    # Need to save the full image somewhere
    settings = MainSettingsController()
    if os.path.basename(settings.get_current_project()) != DEFAULT_PROJECT:
        path = os.path.join(settings.get_current_project(), 'resources', 'combat_effects')
        RESOURCES.combat_effects.save_image(path, foreground_effect)
        RESOURCES.combat_effects.save_image(path, background_effect)

    QMessageBox.information(None, "Spell Import Complete", f"Import of {fn} complete as {controller_effect.nid}")
