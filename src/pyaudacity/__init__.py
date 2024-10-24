"""PyAudacity
By Al Sweigart al@inventwithpython.com

A Python module to control a running instance of Audacity through its macro system."""

# TODO - Bring up to the Audacity team that there's no way for the macros to just move the cursor to a timestamp in the project because there's no menu item for this. But there's literally no way to start a new project and create, like, a 1-second silence.

# TODO - Go through and create enums for the enum parameters to help people working with type-aware IDEs.

# TODO - Go through and check the online Audacity documentation for incorrect default
# values compared to the default values that appear in the various dialog boxes.

# TODO - Need to go through the docstrings and write up my own description (and explain the parameters and units), as well as add a link to the extended online docs.

"""
NOTE: PyAudacity has a general practice of using names and values from the
user interface rather than the Audacity macro documentation.

For example, for the LabelSounds macro, instead of the macro parameter names
we use their UI names:
    threshold_db    -> threshold_level
    measurement     -> threshold_measurement
    sil-dur         -> min_silence_duration
    snd-dur         -> min_label_interval
    type            -> label_type
    pre-offset      -> max_leading_silence
    post-offset     -> max_trailing_silence
    text            -> label_text

The same goes for values. For LabelSounds' threshold_measurement argument, we
take these values:
    'peak'  -> 'Peak level'
    'avg'   -> 'Average level'
    'rms'   -> 'RMS level'

(Enums are also provided for these values.)

The reasoning behind this is that the Audacity macros have very programmer-y
names instead of descriptive ones. Most likely the user of PyAudacity is going
to use positional arguments. But if they do use keyword arguments, the code
might as well be descriptive because code is read more often than it is
written.

The point of PyAudacity is to be easier to use than the dev just writing
to Audacity's named pipes themselves, so we might as well lean into that
direction all the way.

The names are based on the user interface as they appear in Audacity 3.2.5.
"""


__version__ = "0.1.2"

import os, sys, time
from pathlib import Path
from typing import Union, Optional, Tuple, List, Dict

from .enums import (
    ChirpWaveform, 
    ChirpInterpolation,
    DelayType,
    FadeType,
    FadeUnits, 
    NoiseType,
    PitchType,
    RhythmTrackBeatSound,
    Rolloff, 
    ToneWaveform, 
    PluckFade,
    YesNo
)


# PyAudacity has functions called open() and print(), so save the originals:
_open = open
_type = type
_format = format


class PyAudacityException(Exception):
    """The base exception class for PyAudacity-related exceptions."""

    pass


# Taking out the interactive warning stuff, since almost everything requires interaction.
# ("Interaction" meaning macros that could cause pop up dialogs that interrupt automation.)
# NON_INTERACTIVE_MODE = True  # type: bool
#
# def _requireInteraction():  # type: () -> None
#    if NON_INTERACTIVE_MODE:
#        raise RequiresInteractionException()
#
# class RequiresInteractionException(PyAudacityException):
#    """Raised when a macro that requires human user interaction (such as
#    selecting a file in the Open File dialog) was attempted while
#    NON_INTERACTIVE_MODE was set to True."""
#
#    pass


def do(command):  # type: (str) -> str
    if sys.platform == "win32":
        write_pipe_name = "\\\\.\\pipe\\ToSrvPipe"
        read_pipe_name = "\\\\.\\pipe\\FromSrvPipe"
        eol = "\r\n\0"
    else:
        write_pipe_name = "/tmp/audacity_script_pipe.to." + str(os.getuid())
        read_pipe_name = "/tmp/audacity_script_pipe.from." + str(os.getuid())
        eol = "\n"

    if not os.path.exists(write_pipe_name):
        raise PyAudacityException(
            write_pipe_name
            + " does not exist.  Ensure Audacity is running and mod-script-pipe is set to Enabled in the Preferences window."
        )
        sys.exit()

    # For reasons unknown, we need a slight pause after checking for the existence of the read file on Windows:
    time.sleep(0.0001)

    if not os.path.exists(read_pipe_name):
        raise PyAudacityException(
            read_pipe_name
            + " does not exist.  Ensure Audacity is running and mod-script-pipe is set to Enabled in the Preferences window."
        )
        sys.exit()

    # For reasons unknown, we need a slight pause after checking for the existence of the read file on Windows:
    time.sleep(0.0001)

    write_pipe = _open(write_pipe_name, "w")
    read_pipe = _open(read_pipe_name)

    write_pipe.write(command + eol)
    write_pipe.flush()

    response = ""
    line = ""
    while True:
        response += line
        line = read_pipe.readline()
        if line == "\n" and len(response) > 0:
            break

    write_pipe.close()

    # For reasons unknown, we need a slight pause after closing the write file on Windows:
    time.sleep(0.0001)

    read_pipe.close()

    # sys.stdout.write(response + '\n')  # DEBUG
    if "BatchCommand finished: Failed!" in response:
        raise PyAudacityException(response)

    return response


def new() -> str:
    """Creates a new empty project window, to start working on new or
    imported tracks.

    NOTE: The macros issued from pyaudacity always apply to the last Audacity
    window opened. There's no way to pick which Audacity window macros are
    applied to."""
    return do("New")


# The open() function uses the OpenProject2 macro, not the Open macro which only opens the Open dialog.
def open(filename: Path | str, add_to_history: bool = False) -> str:
    """Presents a standard dialog box where you can select either audio files, a list of files (.LOF) or an Audacity Project file to open."""

    if not isinstance(filename, (Path, str)):
        raise PyAudacityException(
            "filename argument must be a Path or str, not" + str(type(add_to_history))
        )

    if not Path(filename).exists():
        raise PyAudacityException(str(filename) + " file not found.")
    if not isinstance(add_to_history, bool):
        raise PyAudacityException(
            "add_to_history argument must be a bool, not" + str(type(add_to_history))
        )

    return do(
        'OpenProject2: Filename="{}" AddToHistory="{}"'.format(filename, add_to_history)
    )


def close() -> str:
    """TODO

    Audacity Documentation: Closes the current project window, prompting you to save your work if you have not saved.
    """
    return do("Close")


def page_setup() -> str:
    """TODO

    Audacity Documentation: Opens the standard Page Setup dialog box prior to printing.
    """
    return do("PageSetup")


def print() -> str:
    """TODO

    Audacity Documentation: Prints all the waveforms in the current project window (and the contents of Label Tracks or other tracks), with the Timeline above. Everything is printed to one page.
    """
    return do("Print")


def exit() -> str:
    """TODO

    Audacity Documentation: Closes all project windows and exits Audacity. If there are any unsaved changes to your project, Audacity will ask if you want to save them.
    """
    return do("Exit")


# The save() function uses the SaveProject2 macro, not the Save macro which only opens the Save dialog.
def save(filename: Path | str,
         add_to_history: bool = False,
         compress: bool = False,
         allow_overwrite: bool = True
         ) -> str:
    """Saves the current Audacity project .AUP3 file."""

    # Audacity will display a pop-up dialog if we try to save with an existing filename.
    if allow_overwrite and Path(filename).exists():
        os.unlink(Path(filename))

    if not isinstance(add_to_history, bool):
        raise PyAudacityException(
            "add_to_history argument must be a bool, not" + str(type(add_to_history))
        )
    if not isinstance(compress, bool):
        raise PyAudacityException(
            "compress argument must be a bool, not" + str(type(compress))
        )

    return do(
        'SaveProject2: Filename="{}" AddToHistory="{}" Compress="{}"'.format(
            filename, add_to_history, compress
        )
    )


def save_as() -> str:
    """TODO

    Audacity Documentation: Same as save(), but allows you to save a copy of an open project
    to a different name or location."""

    return do("SaveAs")


def export_mp3() -> str:
    """TODO

    Audacity Documentation: Exports to an MP3 file."""

    return do("ExportMp3")


def export_wav() -> str:
    """TODO

    Audacity Documentation: Exports to an WAV file."""

    return do("ExportWav")


def export_ogg() -> str:
    """TODO

    Audacity Documentation: Exports to an OGG file."""

    return do("ExportOgg")


# The export() function uses the Export2 macro, not the Export macro which only opens the Export Audio dialog.
def export(filename: Path | str, num_channels: int = 1) -> str:
    """TODO

    Audacity Documentation: Exports selected audio to a named file. This version of export has the full set of export options. However, a current limitation is that the detailed option settings are always stored to and taken from saved preferences. The net effect is that for a given format, the most recently used options for that format will be used. In the current implementation, NumChannels should be 1 (mono) or 2 (stereo).
    """

    if not os.path.exists(filename):
        raise PyAudacityException(str(filename) + " file not found.")
    if not isinstance(num_channels, int):
        raise PyAudacityException(
            "num_channels argument must be a int, not" + str(type(num_channels))
        )

    return do('Export2: Filename="{}" NumChannels="{}"'.format(filename, num_channels))


def export_sel() -> str:
    """TODO

    Audacity Documentation: Opens the Export Audio dialog to export the selected audio.
    """

    return do("ExportSel")


def export_labels() -> str:
    """TODO

    Audacity Documentation: Opens the Exports Labels dialog."""

    return do("ExportLabels")


def export_multiple() -> str:
    """TODO

    Audacity Documentation: Opens the Exports Multiple dialog."""

    return do("ExportMultiple")


def export_midi() -> str:
    """TODO

    Audacity Documentation: Opens the Export MIDI As dialog."""

    return do("ExportMIDI")


# The import_audio() function uses the Import2 macro, not the ImportAudio macro which only opens the Import Audio dialog.
def import_audio(filename: Path | str) -> str: # Union[str, Path]
    """TODO

    Audacity Documentation: Imports from a file. The automation command uses a text box to get the file name rather than a normal file-open dialog.

    Note that this function is named import_audio() because import is a Python keyword.
    """

    if not os.path.exists(filename):
        raise PyAudacityException(str(filename) + " file not found.")

    return do("ImportAudio")


def import_labels() -> str:
    """TODO

    Audacity Documentation: Open the Import Labels dialog."""

    return do("ImportLabels")


def import_midi() -> str:
    """TODO

    Audacity Documentation: Opens the Import MIDI dialog."""

    return do("ImportMIDI")


def import_raw() -> str:
    """TODO

    Audacity Documentation: Opens the Import Raw dialog."""

    return do("ImportRaw")


def undo() -> str:
    """TODO

    Audacity Documentation: Undoes the most recent editing action."""

    return do("Undo")


def redo() -> str:
    """TODO

    Audacity Documentation: Redoes the most recently undone editing action."""

    return do("Redo")


def cut() -> str:
    """TODO

    Audacity Documentation: Removes the selected audio data and/or labels and places these on the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """

    return do("Cut")


def delete() -> str:
    """TODO

    Audacity Documentation: Removes the selected audio data and/or labels without copying these to the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("Delete")


def copy() -> str:
    """TODO

    Audacity Documentation: Copies the selected audio data to the Audacity clipboard without removing it from the project.
    """
    return do("Copy")


def paste() -> str:
    """TODO

    Audacity Documentation: Inserts whatever is on the Audacity clipboard at the position of the selection cursor in the project, replacing whatever audio data is currently selected, if any.
    """
    return do("Paste")


def duplicate() -> str:
    """TODO

    Audacity Documentation: Creates a new track containing only the current selection as a new clip.
    """
    return do("Duplicate")


def edit_meta_data() -> str:
    """TODO

    Audacity Documentation: Open the Edit Metadata Tags dialog."""
    return do("EditMetaData")


def preferences() -> str:
    """TODO

    Audacity Documentation: Open the Preferences dialog."""
    return do("Preferences")


def split_cut() -> str:
    """TODO

    Audacity Documentation: Same as Cut, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitCut")


def split_delete() -> str:
    """TODO

    Audacity Documentation: Same as Delete, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitDelete")


def silence() -> str:
    """TODO

    Audacity Documentation: Replaces the currently selected audio with absolute silence. Does not affect label tracks.
    """
    return do("Silence")


def trim() -> str:
    """TODO

    Audacity Documentation: Deletes all audio but the selection. If there are other separate clips in the same track these are not removed or shifted unless trimming the entire length of a clip or clips. Does not affect label tracks.
    """
    return do("Trim")


def split() -> str:
    """TODO

    Audacity Documentation: Splits the current clip into two clips at the cursor point, or into three clips at the selection boundaries.
    """
    return do("Split")


def split_new() -> str:
    """TODO

    Audacity Documentation: Does a Split Cut on the current selection in the current track, then creates a new track and pastes the selection into the new track.
    """
    return do("SplitNew")


def join() -> str:
    """TODO

    Audacity Documentation: If you select an area that overlaps one or more clips, they are all joined into one large clip. Regions in-between clips become silence.
    """
    return do("Join")


def disjoin() -> str:
    """TODO

    Audacity Documentation: In a selection region that includes absolute silences, creates individual non-silent clips between the regions of silence. The silence becomes blank space between the clips.
    """
    return do("Disjoin")


def edit_labels() -> str:
    """TODO

    Audacity Documentation: Open the Edit Labels dialog."""
    return do("EditLabels")


def add_label() -> str:
    """TODO

    Audacity Documentation: Creates a new, empty label at the cursor or at the selection region.
    """
    return do("AddLabel")


def add_label_playing() -> str:
    """TODO

    Audacity Documentation: Creates a new, empty label at the current playback or recording position.
    """
    return do("AddLabelPlaying")


def paste_new_label() -> str:
    """TODO

    Audacity Documentation: Pastes the text on the Audacity clipboard at the cursor position in the currently selected label track. If there is no selection in the label track a point label is created. If a region is selected in the label track a region label is created. If no label track is selected one is created, and a new label is created.
    """
    return do("PasteNewLabel")


def type_to_create_label() -> str:
    """TODO

    Audacity Documentation: Creates a new label and allows the user to type to fill it out.
    """
    return do("TypeToCreateLabel")


def cut_labels() -> str:
    """TODO

    Audacity Documentation: Removes the selected labels and places these on the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("CutLabels")


def delete_labels() -> str:
    """TODO

    Audacity Documentation: Removes the selected labels without copying these to the Audacity clipboard. By default, any audio or labels to right of the selection are shifted to the left.
    """
    return do("DeleteLabels")


def split_cut_labels() -> str:
    """TODO

    Audacity Documentation: Removes the selected labels and places these on the Audacity clipboard, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitCutLabels")


def split_delete_labels() -> str:
    """TODO

    Audacity Documentation: Removes the selected labels without copying these to the Audacity clipboard, but none of the audio data or labels to right of the selection are shifted.
    """
    return do("SplitDeleteLabels")


def copy_labels() -> str:
    """TODO

    Audacity Documentation: Copies the selected labels to the Audacity clipboard without removing it from the project.
    """
    return do("CopyLabels")


def split_labels() -> str:
    """TODO

    Audacity Documentation: Splits the current labeled audio regions into two regions at the cursor point, or into three regions at the selection boundaries.
    """
    return do("SplitLabels")


def join_labels() -> str:
    """TODO

    Audacity Documentation: If you select an area that overlaps one or more labeled audio regions, they are all joined into one large clip.
    """
    return do("JoinLabels")


def disjoin_labels() -> str:
    """TODO

    Audacity Documentation: Same as the Detach at Silences command, but operates on labeled audio regions.
    """
    return do("DisjoinLabels")


def select_all() -> str:
    """TODO

    Audacity Documentation: Selects all of the audio in all of the tracks."""
    return do("SelectAll")


def select_none() -> str:
    """TODO

    Audacity Documentation: Deselects all of the audio in all of the tracks."""
    return do("SelectNone")


def sel_cursor_stored_cursor() -> str:
    """TODO

    Audacity Documentation: Selects from the position of the cursor to the previously stored cursor position.
    """
    return do("SelCursorStoredCursor")


def store_cursor_position() -> str:
    """TODO

    Audacity Documentation: Stores the current cursor position for use in a later selection.
    """
    return do("StoreCursorPosition")


def zero_cross() -> str:
    """TODO

    Audacity Documentation: Moves the edges of a selection region (or the cursor position) slightly so they are at a rising zero crossing point.
    """
    return do("ZeroCross")


def sel_all_tracks() -> str:
    """TODO

    Audacity Documentation: Extends the current selection up and/or down into all tracks in the project.
    """
    return do("SelAllTracks")


def sel_sync_lock_tracks() -> str:
    """TODO

    Audacity Documentation: Extends the current selection up and/or down into all sync-locked tracks in the currently selected track group.
    """
    return do("SelSyncLockTracks")


def left_at_playback_position() -> str:
    """TODO

    Audacity Documentation: When Audacity is playing, recording or paused, sets the left boundary of a potential selection by moving the cursor to the current position of the green playback cursor (or red recording cursor). Otherwise, opens the "Set Left Selection Boundary" dialog for adjusting the time position of the left-hand selection boundary. If there is no selection, moving the time digits backwards creates a selection ending at the former cursor position, and moving the time digits forwards provides a way to move the cursor forwards to an exact point.
    """
    return do("Left at Playback Position")


def right_at_playback_position() -> str:
    """TODO

    Audacity Documentation: When Audacity is playing, recording or paused, sets the right boundary of the selection, thus drawing the selection from the cursor position to the current position of the green playback cursor (or red recording cursor). Otherwise, opens the "Set Right Selection Boundary" dialog for adjusting the time position of the right-hand selection boundary. If there is no selection, moving the time digits forwards creates a selection starting at the former cursor position, and moving the time digits backwards provides a way to move the cursor backwards to an exact point.
    """
    return do("Right at Playback Position")


def sel_track_start_to_cursor() -> str:
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the start of the track to the cursor position.
    """
    return do("SelTrackStartToCursor")


def sel_cursor_to_track_end() -> str:
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the cursor position to the end of the track.
    """
    return do("SelCursorToTrackEnd")


def sel_track_start_to_end() -> str:
    """TODO

    Audacity Documentation: Selects a region in the selected track(s) from the start of the track to the end of the track.
    """
    return do("SelTrackStartToEnd")


def sel_save() -> str:
    """TODO

    Audacity Documentation: Stores the end points of a selection for later reuse."""
    return do("SelSave")


def sel_restore() -> str:
    """TODO

    Audacity Documentation: Retrieves the end points of a previously stored selection.
    """
    return do("SelRestore")


def toggle_spectral_selection() -> str:
    """TODO

    Audacity Documentation: Changes between selecting a time range and selecting the last selected spectral selection in that time range. This command toggles the spectral selection even if not in Spectrogram view, but you must be in Spectrogram view to use the spectral selection in one of the Spectral edit effects.
    """
    return do("ToggleSpectralSelection")


def next_higher_peak_frequency() -> str:
    """TODO

    Audacity Documentation: When in Spectrogram view, snaps the center frequency to the next higher frequency peak, moving the spectral selection upwards.
    """
    return do("NextHigherPeakFrequency")


def next_lower_peak_frequency() -> str:
    """TODO

    Audacity Documentation: When in Spectrogram views snaps the center frequency to the next lower frequency peak, moving the spectral selection downwards.
    """
    return do("NextLowerPeakFrequency")


def sel_prev_clip_boundary_to_cursor() -> str:
    """TODO

    Audacity Documentation: Selects from the current cursor position back to the right-hand edge of the previous clip.
    """
    return do("SelPrevClipBoundaryToCursor")


def sel_cursor_to_next_clip_boundary() -> str:
    """TODO

    Audacity Documentation: Selects from the current cursor position forward to the left-hand edge of the next clip.
    """
    return do("SelCursorToNextClipBoundary")


def sel_prev_clip() -> str:
    """TODO

    Audacity Documentation: Moves the selection to the previous clip."""
    return do("SelPrevClip")


def sel_next_clip() -> str:
    """TODO

    Audacity Documentation: Moves the selection to the next clip."""
    return do("SelNextClip")


def undo_history() -> str:
    """TODO

    Audacity Documentation: Brings up the History window which can then be left open while using Audacity normally. History lists all undoable actions performed in the current project, including importing.
    """
    return do("UndoHistory")


def karaoke() -> str:
    """TODO

    Audacity Documentation: Brings up the Karaoke window, which displays the labels in a "bouncing ball" scrolling display.
    """
    return do("Karaoke")


def mixer_board() -> str:
    """TODO

    Audacity Documentation: Mixer Board is an alternative view to the audio tracks in the main tracks window. Analogous to a hardware mixer board, each audio track is displayed in a Track Strip.
    """
    return do("MixerBoard")


def show_extra_menus() -> str:
    """TODO

    Audacity Documentation: Shows extra menus with many extra less-used commands."""
    return do("ShowExtraMenus")


def show_clipping() -> str:
    """TODO

    Audacity Documentation: Option to show or not show audio that is too loud (in red) on the wave form.
    """
    return do("ShowClipping")


def zoom_in() -> str:
    """TODO

    Audacity Documentation: Zooms in on the horizontal axis of the audio displaying more detail over a shorter length of time.
    """
    return do("ZoomIn")


def zoom_normal() -> str:
    """TODO

    Audacity Documentation: Zooms to the default view which displays about one inch per second.
    """
    return do("ZoomNormal")


def zoom_out() -> str:
    """TODO

    Audacity Documentation: Zooms out displaying less detail over a greater length of time.
    """
    return do("ZoomOut")


def zoom_sel() -> str:
    """TODO

    Audacity Documentation: Zooms in or out so that the selected audio fills the width of the window.
    """
    return do("ZoomSel")


def zoom_toggle() -> str:
    """TODO

    Audacity Documentation: Changes the zoom back and forth between two preset levels.
    """
    return do("ZoomToggle")


def advanced_v_zoom() -> str:
    """TODO

    Audacity Documentation: Enable for left-click gestures in the vertical scale to control zooming.
    """
    return do("AdvancedVZoom")


def fit_in_window() -> str:
    """TODO

    Audacity Documentation: Zooms out until the entire project just fits in the window.
    """
    return do("FitInWindow")


def fit_v() -> str:
    """TODO

    Audacity Documentation: Adjusts the height of all the tracks until they fit in the project window.
    """
    return do("FitV")


def collapse_all_tracks() -> str:
    """TODO

    Audacity Documentation: Collapses all tracks to take up the minimum amount of space.
    """
    return do("CollapseAllTracks")


def expand_all_tracks() -> str:
    """TODO

    Audacity Documentation: Expands all collapsed tracks to their original size before the last collapse.
    """
    return do("ExpandAllTracks")


def skip_sel_start() -> str:
    """TODO

    Audacity Documentation: When there is a selection, moves the cursor to the start of the selection and removes the selection.
    """
    return do("SkipSelStart")


def skip_sel_end() -> str:
    """TODO

    Audacity Documentation: When there is a selection, moves the cursor to the end of the selection and removes the selection.
    """
    return do("SkipSelEnd")


def reset_toolbars() -> str:
    """TODO

    Audacity Documentation: Using this command positions all toolbars in default location and size as they were when Audacity was first installed.
    """
    return do("ResetToolbars")


def show_transport_t_b() -> str:
    """TODO

    Audacity Documentation: Controls playback and recording and skips to start or end of project when neither playing or recording.
    """
    return do("ShowTransportTB")


def show_tools_t_b() -> str:
    """TODO

    Audacity Documentation: Chooses various tools for selection, volume adjustment, zooming and time-shifting of audio.
    """
    return do("ShowToolsTB")


def show_record_meter_t_b() -> str:
    """TODO

    Audacity Documentation: Displays recording levels and toggles input monitoring when not recording.
    """
    return do("ShowRecordMeterTB")


def show_play_meter_t_b() -> str:
    """TODO

    Audacity Documentation: Displays playback levels."""
    return do("ShowPlayMeterTB")


def show_mixer_t_b() -> str:
    """TODO

    Audacity Documentation: Adjusts the recording and playback volumes of the devices currently selected in Device Toolbar.
    """
    return do("ShowMixerTB")


def show_edit_t_b() -> str:
    """TODO

    Audacity Documentation: Cut, copy, paste, trim audio, silence audio, undo, redo, zoom tools.
    """
    return do("ShowEditTB")


def show_transcription_t_b() -> str:
    """TODO

    Audacity Documentation: Plays audio at a slower or faster speed than normal, affecting pitch.
    """
    return do("ShowTranscriptionTB")


def show_scrubbing_t_b() -> str:
    """TODO

    Audacity Documentation: Controls playback and recording and skips to start or end of project when neither playing or recording.
    """
    return do("ShowScrubbingTB")


def show_device_t_b() -> str:
    """TODO

    Audacity Documentation: Selects audio host, recording device, number of recording channels and playback device.
    """
    return do("ShowDeviceTB")


def show_selection_t_b() -> str:
    """TODO

    Audacity Documentation: Controls the sample rate of the project, snapping to the selection format and adjusts cursor and region position by keyboard input.
    """
    return do("ShowSelectionTB")


def show_spectral_selection_t_b() -> str:
    """TODO

    Audacity Documentation: Displays and lets you adjust the current spectral (frequency) selection without having to be in Spectrogram view.
    """
    return do("ShowSpectralSelectionTB")


def rescan_devices() -> str:
    """TODO

    Audacity Documentation: Rescan for audio devices connected to your computer, and update the playback and recording dropdown menus in Device Toolbar.
    """
    return do("RescanDevices")


def play_stop() -> str:
    """TODO

    Audacity Documentation: Starts and stops playback or stops a recording (stopping does not change the restart position). Therefore using any play or record command after stopping with "Play/Stop" will start playback or recording from the same Timeline position it last started from. You can also assign separate shortcuts for Play and Stop.
    """
    return do("PlayStop")


def play_stop_select() -> str:
    """TODO

    Audacity Documentation: Starts playback like "Play/Stop", but stopping playback sets the restart position to the stop point. When stopped, this command is the same as "Play/Stop". When playing, this command stops playback and moves the cursor (or the start of the selection) to the position where playback stopped.
    """
    return do("PlayStopSelect")


def pause() -> str:
    """TODO

    Audacity Documentation: Temporarily pauses playing or recording without losing your place.
    """
    return do("Pause")


def record1st_choice() -> str:
    """TODO

    Audacity Documentation: Starts recording at the end of the currently selected track(s).
    """
    return do("Record1stChoice")


def record2nd_choice() -> str:
    """TODO

    Audacity Documentation: Recording begins on a new track at either the current cursor location or at the beginning of the current selection.
    """
    return do("Record2ndChoice")


def timer_record() -> str:
    """TODO

    Audacity Documentation: Brings up the Timer Record dialog."""
    return do("TimerRecord")


def punch_and_roll() -> str:
    """TODO

    Audacity Documentation: Re-record over audio, with a pre-roll of audio that comes before.
    """
    return do("PunchAndRoll")


def scrub() -> str:
    """TODO

    Audacity Documentation: Scrubbing is the action of moving the mouse pointer right or left so as to adjust the position, speed or direction of playback, listening to the audio at the same time.
    """
    return do("Scrub")


def seek() -> str:
    """TODO

    Audacity Documentation: Seeking is similar to Scrubbing except that it is playback with skips, similar to using the seek button on a CD player.
    """
    return do("Seek")


def toggle_scrub_ruler() -> str:
    """TODO

    Audacity Documentation: Shows (or hides) the scrub ruler, which is just below the timeline.
    """
    return do("ToggleScrubRuler")


def curs_sel_start() -> str:
    """TODO

    Audacity Documentation: Moves the left edge of the current selection to the center of the screen, without changing the zoom level.
    """
    return do("CursSelStart")


def curs_sel_end() -> str:
    """TODO

    Audacity Documentation: Moves the right edge of the current selection to the center of the screen, without changing the zoom level.
    """
    return do("CursSelEnd")


def curs_track_start() -> str:
    """TODO

    Audacity Documentation: Moves the cursor to the start of the selected track."""
    return do("CursTrackStart")


def curs_track_end() -> str:
    """TODO

    Audacity Documentation: Moves the cursor to the end of the selected track."""
    return do("CursTrackEnd")


def curs_prev_clip_boundary() -> str:
    """TODO

    Audacity Documentation: Moves the cursor position back to the right-hand edge of the previous clip.
    """
    return do("CursPrevClipBoundary")


def curs_next_clip_boundary() -> str:
    """TODO

    Audacity Documentation: Moves the cursor position forward to the left-hand edge of the next clip.
    """
    return do("CursNextClipBoundary")


def curs_project_start() -> str:
    """TODO

    Audacity Documentation: Moves the cursor to the beginning of the project."""
    return do("CursProjectStart")


def curs_project_end() -> str:
    """TODO

    Audacity Documentation: Moves the cursor to the end of the project."""
    return do("CursProjectEnd")


def sound_activation_level() -> str:
    """TODO

    Audacity Documentation: Sets the activation level above which Sound Activated Recording will record.
    """
    return do("SoundActivationLevel")


def sound_activation() -> str:
    """TODO

    Audacity Documentation: Toggles on and off the Sound Activated Recording option."""
    return do("SoundActivation")


def pinned_head() -> str:
    """TODO

    Audacity Documentation: You can change Audacity to play and record with a fixed head pinned to the Timeline. You can adjust the position of the fixed head by dragging it.
    """
    return do("PinnedHead")


def overdub() -> str:
    """TODO

    Audacity Documentation: Toggles on and off the Overdub option."""
    return do("Overdub")


def s_w_playthrough() -> str:
    """TODO

    Audacity Documentation: Toggles on and off the Software Playthrough option."""
    return do("SWPlaythrough")


def resample() -> str:
    """TODO

    Audacity Documentation: Allows you to resample the selected track(s) to a new sample rate for use in the project.
    """
    return do("Resample")


def remove_tracks() -> str:
    """TODO

    Audacity Documentation: Removes the selected track(s) from the project. Even if only part of a track is selected, the entire track is removed.
    """
    return do("RemoveTracks")


def sync_lock() -> str:
    """TODO

    Audacity Documentation: Ensures that length changes occurring anywhere in a defined group of tracks also take place in all audio or label tracks in that group.
    """
    return do("SyncLock")


def new_mono_track() -> str:
    """TODO

    Audacity Documentation: Creates a new empty mono audio track."""
    return do("NewMonoTrack")


def new_stereo_track() -> str:
    """TODO

    Audacity Documentation: Adds an empty stereo track to the project."""
    return do("NewStereoTrack")


def new_label_track() -> str:
    """TODO

    Audacity Documentation: Adds an empty label track to the project."""
    return do("NewLabelTrack")


def new_time_track() -> str:
    """TODO

    Audacity Documentation: Adds an empty time track to the project. Time tracks are used to speed up and slow down audio.
    """
    return do("NewTimeTrack")


def stereo_to_mono() -> str:
    """TODO

    Audacity Documentation: Converts the selected stereo track(s) into the same number of mono tracks, combining left and right channels equally by averaging the volume of both channels.
    """
    return do("Stereo to Mono")


def mix_and_render() -> str:
    """TODO

    Audacity Documentation: Mixes down all selected tracks to a single mono or stereo track, rendering to the waveform all real-time transformations that had been applied (such as track gain, panning, amplitude envelopes or a change in project rate).
    """
    return do("MixAndRender")


def mix_and_render_to_new_track() -> str:
    """TODO

    Audacity Documentation: Same as Tracks > Mix and Render except that the original tracks are preserved rather than being replaced by the resulting "Mix" track.
    """
    return do("MixAndRenderToNewTrack")


def mute_all_tracks() -> str:
    """TODO

    Audacity Documentation: Mutes all the audio tracks in the project as if you had used the mute buttons from the Track Control Panel on each track.
    """
    return do("MuteAllTracks")


def unmute_all_tracks() -> str:
    """TODO

    Audacity Documentation: Unmutes all the audio tracks in the project as if you had released the mute buttons from the Track Control Panel on each track.
    """
    return do("UnmuteAllTracks")


def mute_tracks() -> str:
    """TODO

    Audacity Documentation: Mutes the selected tracks."""
    return do("MuteTracks")


def unmute_tracks() -> str:
    """TODO

    Audacity Documentation: Unmutes the selected tracks."""
    return do("UnmuteTracks")


def pan_left() -> str:
    """TODO

    Audacity Documentation: Pan selected audio to left speaker."""
    return do("PanLeft")


def pan_right() -> str:
    """TODO

    Audacity Documentation: Pan selected audio centrally."""
    return do("PanRight")


def pan_center() -> str:
    """TODO

    Audacity Documentation: Pan selected audio to right speaker."""
    return do("PanCenter")


def align__end_to_end() -> str:
    """TODO

    Audacity Documentation: Aligns the selected tracks one after the other, based on their top-to-bottom order in the project window.
    """
    return do("Align_EndToEnd")


def align__together() -> str:
    """TODO

    Audacity Documentation: Align the selected tracks so that they start at the same (averaged) start time.
    """
    return do("Align_Together")


def align__start_to_zero() -> str:
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the start of the project.
    """
    return do("Align_StartToZero")


def align__start_to_sel_start() -> str:
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the current cursor position or with the start of the current selection.
    """
    return do("Align_StartToSelStart")


def align__start_to_sel_end() -> str:
    """TODO

    Audacity Documentation: Aligns the start of selected tracks with the end of the current selection.
    """
    return do("Align_StartToSelEnd")


def align__end_to_sel_start() -> str:
    """TODO

    Audacity Documentation: Aligns the end of selected tracks with the current cursor position or with the start of the current selection.
    """
    return do("Align_EndToSelStart")


def align__end_to_sel_end() -> str:
    """TODO

    Audacity Documentation: Aligns the end of selected tracks with the end of the current selection.
    """
    return do("Align_EndToSelEnd")


def move_selection_with_tracks() -> str:
    """TODO

    Audacity Documentation: Toggles on/off the selection moving with the realigned tracks, or staying put.
    """
    return do("MoveSelectionWithTracks")


def sort_by_time() -> str:
    """TODO

    Audacity Documentation: Sort tracks in order of start time."""
    return do("SortByTime")


def sort_by_name() -> str:
    """TODO

    Audacity Documentation: Sort tracks in order by name."""
    return do("SortByName")


def manage_generators() -> str:
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageGenerators")


def built_in() -> str:
    """TODO

    Audacity Documentation: Shows the list of available Audacity built-in effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("Built-in")


def nyquist() -> str:
    """TODO

    Audacity Documentation: Shows the list of available Nyquist effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("Nyquist")




def chirp(
    start_frequency: float = 440.0,
    end_frequency: float = 1320.0,
    start_amplitude: float = 0.8,
    end_amplitude: float = 0.1,
    waveform: ChirpWaveform | str = ChirpWaveform.SINE,
    interpolation: ChirpInterpolation | str = ChirpInterpolation.LINEAR,
) -> str:
    """TODO

    Audacity Documentation: Generates four different types of tone waveforms like the Tone Generator, but additionally allows setting of the starting and ending amplitude and frequency.
    """

    waveform, interpolation = str(waveform), str(interpolation)

    # Argument type checks:
    if not isinstance(start_frequency, (float, int)):
        raise PyAudacityException(
            "start_frequency argument must be float or int, not "
            + str(type(start_frequency))
        )
    if not isinstance(end_frequency, (float, int)):
        raise PyAudacityException(
            "end_frequency argument must be float or int, not "
            + str(type(end_frequency))
        )
    if not isinstance(start_amplitude, (float, int)):
        raise PyAudacityException(
            "start_amplitude argument must be float or int, not "
            + str(type(start_amplitude))
        )
    if not isinstance(end_amplitude, (float, int)):
        raise PyAudacityException(
            "end_amplitude argument must be float or int, not "
            + str(type(end_amplitude))
        )

    # Argument value checks:
    if waveform.lower() not in ("sine", "square", "sawtooth", "square, no alias"):
        raise PyAudacityException(
            'waveform argument must be one of "Sine", "Square", "Sawtooth", or "Square, no alias"'
        )
    if interpolation.lower() not in ("linear", "logarithmic"):
        raise PyAudacityException(
            'interpolation argument must be one of "Linear" or "Logarithmic"'
        )

    if not (0.0 <= start_amplitude <= 1.0):
        raise PyAudacityException(
            "start_amplitude argument must be between 0.0 and 1.0"
        )
    if not (0.0 <= end_amplitude <= 1.0):
        raise PyAudacityException("end_amplitude argument must be between 0.0 and 1.0")
    if start_frequency < 0:
        raise PyAudacityException("start_frequency must be positive")
    if end_frequency < 0:
        raise PyAudacityException("end_frequency must be positive")

    # Convert str args to their expected case:
    waveform = waveform[0].upper() + waveform[1:].lower()
    interpolation = interpolation.title()

    # Run macro:
    return do(
        'Chirp: StartFreq="{}" EndFreq="{}" StartAmp="{}" EndAmp="{}" Waveform="{}" Interpolation="{}"'.format(
            start_frequency,
            end_frequency,
            start_amplitude,
            end_amplitude,
            waveform,
            interpolation,
        )
    )


def noise(noise_type: NoiseType | str = NoiseType.WHITE, amplitude: float = 0.8):
    valid_noise_types = [item.value for item in NoiseType]
    if noise_type not in valid_noise_types:
        raise PyAudacityException(
            f'noise_type argument must be one of {valid_noise_types}, got "{noise_type}"'
        )

    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            f"amplitude argument must be float or int, not {type(amplitude)}"
        )
    if not (0.0 <= amplitude <= 1.0):
        raise PyAudacityException("amplitude argument must be between 0.0 and 1.0")

    return do(f'Noise: Type="{noise_type}" Amplitude="{amplitude}"')





def tone(frequency: float = 440.0, amplitude: float = 0.8, waveform: str | ToneWaveform = ToneWaveform.SINE) -> str:
    """TODO

    Audacity Documentation: Generates one of four different tone waveforms: Sine, Square, Sawtooth or Square (no alias), and a frequency between 1 Hz and half the current project rate.
    """

    # TODO - NOTE: The documentation is wrong; there doesn't seem to be an "Interpolation" parameter anymore for Tone.

    waveform = str(waveform)

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            "amplitude argument must be float or int, not " + str(type(amplitude))
        )
    if waveform.lower() not in ("sine", "square", "sawtooth", "square, no alias"):
        raise PyAudacityException(
            'waveform argument must be one of "Sine", "Square", "Sawtooth", or "Square, no alias"'
        )

    waveform = waveform[0].upper() + waveform[1:].lower()

    return do(
        'Tone: Frequency="{}" Amplitude="{}" Waveform="{}"'.format(
            frequency, amplitude, waveform
        )
    )


def pluck(pitch: int = 60, fade: PluckFade | str = PluckFade.ABRUPT, duration: float = 1.0) -> str:
    """TODO

    Audacity Documentation: A synthesized pluck tone with abrupt or gradual fade-out, and selectable pitch corresponding to a MIDI note.
    """

    # NOTE: A region of a track must be selected. It's not enough to just set the cursor where you want the pluck to begin. The length of the selected region is, however, ignored.

    fade = str(fade).title()

    if not isinstance(pitch, int):
        raise PyAudacityException("pitch argument must be int, not " + str(type(pitch)))
    if not isinstance(duration, (float, int)):
        raise PyAudacityException(
            "duration argument must be float or int, not " + str(type(duration))
        )
    if fade not in ("Abrupt", "Gradual"):
        raise PyAudacityException('fade argument must be one of "Abrupt" or "Gradual"')

    # The user interface says 60 seconds is the max duration.
    if duration > 60:
        raise PyAudacityException(
            "duration is larger than the 60 seconds maximum allowed limit"
        )

    # Note: The parameter names are lowercase in the documentation so I'm making them lowercase here.
    # https://manual.audacityteam.org/man/scripting_reference.html
    return do('Pluck: pitch="{}" fade="{}" dur="{}"'.format(pitch, fade, duration))



def rhythm_track(
    tempo: float = 120.0,
    beats_per_bar: int = 4,
    swing: float = 0.0,
    number_of_bars: int = 16,
    rhythm_track_duration: float = 0.0,
    start_time_offset: float = 0.0,
    beat_sound: RhythmTrackBeatSound | str = RhythmTrackBeatSound.METRONOME,
    pitch_of_strong_beat: int = 84,
    pitch_of_weak_beat: int = 0,
) -> str:
    """TODO

    Audacity Documentation: Generates a track with regularly spaced sounds at a specified tempo and number of beats per measure (bar).
    """

    beat_sound = str(beat_sound)

    if not isinstance(tempo, (float, int)):
        raise PyAudacityException(
            "tempo argument must be float or int, not " + str(type(tempo))
        )
    if not isinstance(beats_per_bar, int):
        raise PyAudacityException(
            "beats_per_bar argument must be int, not " + str(type(beats_per_bar))
        )
    if not isinstance(swing, (float, int)):
        raise PyAudacityException(
            "swing argument must be float or int, not " + str(type(swing))
        )
    if not isinstance(number_of_bars, int):
        raise PyAudacityException(
            "number_of_bars argument must be int, not " + str(type(number_of_bars))
        )
    if not isinstance(rhythm_track_duration, (float, int)):
        raise PyAudacityException(
            "rhythm_track_duration argument must be float or int, not "
            + str(type(rhythm_track_duration))
        )
    if not isinstance(start_time_offset, (float, int)):
        raise PyAudacityException(
            "start_time_offset argument must be float or int, not "
            + str(type(start_time_offset))
        )
    if beat_sound.lower() not in (
        "metronome tick",
        "ping (short)",
        "ping (long)",
        "cowbell",
        "resonant noise",
        "noise click",
        "drip (short)",
        "drip (long)",
    ):
        raise PyAudacityException(
            'beat_sound argument must be one of "Abrupt" or "Gradual"'
        )
    if not isinstance(pitch_of_strong_beat, int):
        raise PyAudacityException(
            "pitch_of_strong_beat argument must be int, not "
            + str(type(pitch_of_strong_beat))
        )
    if not isinstance(pitch_of_weak_beat, int):
        raise PyAudacityException(
            "pitch_of_weak_beat argument must be int, not "
            + str(type(pitch_of_weak_beat))
        )

    beat_sound = {
        "metronome tick": "Metronome",
        "ping (short)": "Ping (short)",
        "ping (long)": "Ping (long)",
        "cowbell": "Cowbell",
        "resonant noise": "ResonantNoise",
        "noise click": "NoiseClick",
        "drip (short)": "Drip (short)",
        "drip (long)": "Drip (long)",
    }[beat_sound.lower()]

    # The documentation has the parameters as lowercase, so I do too:
    return do(
        'RhythmTrack: tempo="{}" timesig="{}" swing="{}" bars="{}" click-track-dur="{}" offset="{}" click-type="{}" high="{}" low="{}"'.format(
            tempo,
            beats_per_bar,
            swing,
            number_of_bars,
            rhythm_track_duration,
            start_time_offset,
            beat_sound,
            pitch_of_strong_beat,
            pitch_of_weak_beat,
        )
    )


def risset_drum(
    frequency: float = 0.0,
    decay: float = 0.0,
    center_frequency_of_noise: float = 0.0,
    width_of_noise_band: float = 0.0,
    noise: float = 0.0,
    gain: float = 0.0,
) -> str:
    """TODO

    Audacity Documentation: Produces a realistic drum sound."""

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(decay, (float, int)):
        raise PyAudacityException(
            "decay argument must be float or int, not " + str(type(decay))
        )
    if not isinstance(center_frequency_of_noise, (float, int)):
        raise PyAudacityException(
            "center_frequency_of_noise argument must be float or int, not "
            + str(type(center_frequency_of_noise))
        )
    if not isinstance(width_of_noise_band, (float, int)):
        raise PyAudacityException(
            "width_of_noise_band argument must be float or int, not "
            + str(type(width_of_noise_band))
        )
    if not isinstance(noise, (float, int)):
        raise PyAudacityException(
            "noise argument must be float or int, not " + str(type(noise))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    # The documentation has lowercase parameters, so I do too:
    return do(
        'RissetDrum: freq="{}" decay="{}" cf="{}" bw="{}" noise="{}" gain="{}"'.format(
            frequency,
            decay,
            center_frequency_of_noise,
            width_of_noise_band,
            noise,
            gain,
        )
    )


def manage_effects() -> str:
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageEffects")


def repeat_last_effect() -> str:
    """TODO

    Audacity Documentation: Repeats the last used effect at its last used settings and without displaying any dialog.
    """
    return do("RepeatLastEffect")


def ladspa() -> str:
    """TODO

    Audacity Documentation: Shows the list of available LADSPA effects but only if the user has effects "Grouped by Type" in Effects Preferences.
    """
    return do("LADSPA")


def amplify(ratio: float = 0.9, allow_clipping: bool = False) -> str:
    """TODO

    Audacity Documentation: Increases or decreases the volume of the audio you have selected.
    """

    if not isinstance(ratio, (float, int)):
        raise PyAudacityException(
            "ratio argument must be float or int, not " + str(type(ratio))
        )
    if not isinstance(allow_clipping, bool):
        raise PyAudacityException(
            "allow_clipping argument must be a bool, not" + str(type(allow_clipping))
        )

    return do('Amplify: Ratio="{}" AllowClipping="{}"'.format(ratio, allow_clipping))


def auto_duck(
    duck_amount_db: float = -12.0,
    inner_fade_down_len: float = 0.0,
    inner_fade_up_len: float = 0.0,
    outer_fade_down_len: float = 0.5,
    outer_fade_up_len: float = 0.5,
    threshold_db: float = -30.0,
    maximum_pause: float = 1.0,
) -> str:
    """TODO

    Audacity Documentation: Reduces (ducks) the volume of one or more tracks whenever the volume of a specified "control" track reaches a particular level. Typically used to make a music track softer whenever speech in a commentary track is heard.
    """

    if not isinstance(duck_amount_db, (float, int)):
        raise PyAudacityException(
            "duck_amount_db argument must be float or int, not "
            + str(type(duck_amount_db))
        )
    if not isinstance(inner_fade_down_len, (float, int)):
        raise PyAudacityException(
            "inner_fade_down_len argument must be float or int, not "
            + str(type(inner_fade_down_len))
        )
    if not isinstance(inner_fade_up_len, (float, int)):
        raise PyAudacityException(
            "inner_fade_up_len argument must be float or int, not "
            + str(type(inner_fade_up_len))
        )
    if not isinstance(outer_fade_down_len, (float, int)):
        raise PyAudacityException(
            "outer_fade_down_len argument must be float or int, not "
            + str(type(outer_fade_down_len))
        )
    if not isinstance(outer_fade_up_len, (float, int)):
        raise PyAudacityException(
            "outer_fade_up_len argument must be float or int, not "
            + str(type(outer_fade_up_len))
        )
    if not isinstance(threshold_db, (float, int)):
        raise PyAudacityException(
            "threshold_db argument must be float or int, not " + str(type(threshold_db))
        )
    if not isinstance(maximum_pause, (float, int)):
        raise PyAudacityException(
            "maximum_pause argument must be float or int, not "
            + str(type(maximum_pause))
        )

    return do(
        'AutoDuck: DuckAmountDb="{}" InnerFadeDownLen="{}" InnerFadeUpLen="{}" OuterFadeDownLen="{}" OuterFadeUpLen="{}" ThresholdDb="{}" MaximumPause="{}"'.format(
            duck_amount_db,
            inner_fade_down_len,
            inner_fade_up_len,
            outer_fade_down_len,
            outer_fade_up_len,
            threshold_db,
            maximum_pause,
        )
    )


def bass_and_treble(bass: float = 0.0, treble: float = 0.0, gain: float = 0.0, link_sliders: bool = False) -> str:
    """TODO

    Audacity Documentation: Increases or decreases the lower frequencies and higher frequencies of your audio independently; behaves just like the bass and treble controls on a stereo system.
    """

    if not isinstance(bass, (float, int)):
        raise PyAudacityException(
            "bass argument must be float or int, not " + str(type(bass))
        )
    if not isinstance(treble, (float, int)):
        raise PyAudacityException(
            "treble argument must be float or int, not " + str(type(treble))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )
    if not isinstance(link_sliders, bool):
        raise PyAudacityException(
            "link_sliders argument must be a bool, not" + str(type(link_sliders))
        )

    # TODO - The documentation shows it as "Link Sliders" but I don't know if the space is intentional or not.
    # There's no way to tell since Audacity's macro system doesn't give errors for bad parameter names.
    return do('BassAndTreble: Bass="{}" Treble="{}" Gain="{}" LinkSliders="{}"')


def change_pitch(percentage: float = 0.0, use_high_quality_stretching: bool = False) -> str:
    """TODO

    Audacity Documentation: Change the pitch of a selection without changing its tempo.
    """

    # TODO - the documentation is unclear as to what SBSMS stands for, but it's
    # a bool and the only checkbox in the Change Pitch dialog is the one marked
    # "Use high quality stretching (slow)", and SBSMS and this checkbox are
    # also found in the Change Tempo dialog.
    # I've decided to rename SBSMS to use_high_quality_stretching

    # TODO - there seem to be several fields in the Change Pitch dialog that
    # aren't captured by the parameters for this macro. What's up with that?

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )
    if not isinstance(use_high_quality_stretching, bool):
        raise PyAudacityException(
            "use_high_quality_stretching argument must be a bool, not"
            + str(type(use_high_quality_stretching))
        )

    return do(
        'ChangePitch: Percentage="{}" SBSMS="{}"'.format(
            percentage, use_high_quality_stretching
        )
    )


def change_speed(percentage: float = 0.0) -> str:
    """TODO

    Audacity Documentation: Change the speed of a selection, also changing its pitch."""

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )

    return do('ChangeSpeed: Percentage="{}"'.format(percentage))


def change_tempo(percentage: float = 0.0, use_high_quality_stretching: bool = False) -> str:
    """TODO

    Audacity Documentation: Change the tempo and length (duration) of a selection without changing its pitch.
    """

    if not isinstance(percentage, (float, int)):
        raise PyAudacityException(
            "percentage argument must be float or int, not " + str(type(percentage))
        )
    if not isinstance(use_high_quality_stretching, bool):
        raise PyAudacityException(
            "use_high_quality_stretching argument must be a bool, not"
            + str(type(use_high_quality_stretching))
        )

    return do(
        'ChangeTempo: Percentage="{}" SBSMS="{}"'.format(
            percentage, use_high_quality_stretching
        )
    )


def click_removal(threshold: int = 200, width: int = 20) -> str:
    """TODO

    Audacity Documentation: Click Removal is designed to remove clicks on audio tracks and is especially suited to declicking recordings made from vinyl records.
    """

    if not isinstance(threshold, int):
        raise PyAudacityException(
            "threshold argument must be int, not " + str(type(threshold))
        )
    if not isinstance(width, int):
        raise PyAudacityException("width argument must be int, not " + str(type(width)))

    return do('ClickRemoval: Threshold="{}" Width="{}"'.format(threshold, width))


def compressor(
    threshold: float = -12.0,
    noise_floor: float = -40.0,
    ratio: float = 2.0,
    attack_time: float = 0.2,
    release_time: float = 1.0,
    normalize: bool = True,
    use_peak: bool = False,
) -> str:
    """TODO

    Audacity Documentation: Compresses the dynamic range by two alternative methods. The default "RMS" method makes the louder parts softer, but leaves the quieter audio alone. The alternative "peaks" method makes the entire audio louder, but amplifies the louder parts less than the quieter parts. Make-up gain can be applied to either method, making the result as loud as possible without clipping, but not changing the dynamic range further.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    if not isinstance(noise_floor, (float, int)):
        raise PyAudacityException(
            "noise_floor argument must be float or int, not " + str(type(noise_floor))
        )
    if not isinstance(ratio, (float, int)):
        raise PyAudacityException(
            "ratio argument must be float or int, not " + str(type(ratio))
        )
    if not isinstance(attack_time, (float, int)):
        raise PyAudacityException(
            "attack_time argument must be float or int, not " + str(type(attack_time))
        )
    if not isinstance(release_time, (float, int)):
        raise PyAudacityException(
            "release_time argument must be float or int, not " + str(type(release_time))
        )
    if not isinstance(normalize, bool):
        raise PyAudacityException(
            "normalize argument must be a bool, not" + str(type(normalize))
        )
    if not isinstance(use_peak, bool):
        raise PyAudacityException(
            "use_peak argument must be a bool, not" + str(type(use_peak))
        )

    return do(
        'Compressor: Threshold="{}" NoiseFloor="{}" Ratio="{}" AttackTime="{}" ReleaseTime="{}" Normalize="{}" UsePeak="{}"'.format(
            threshold,
            noise_floor,
            ratio,
            attack_time,
            release_time,
            normalize,
            use_peak,
        )
    )


def echo(delay: float = 1.0, decay: float = 0.5) -> str:
    """TODO

    Audacity Documentation: Repeats the selected audio again and again, normally softer each time and normally not blended into the original sound until some time after it starts. The delay time between each repeat is fixed, with no pause in between each repeat. For a more configurable echo effect with a variable delay time and pitch-changed echoes, see Delay.
    """

    if not isinstance(delay, (float, int)):
        raise PyAudacityException(
            "delay argument must be float or int, not " + str(type(delay))
        )
    if not isinstance(decay, (float, int)):
        raise PyAudacityException(
            "decay argument must be float or int, not " + str(type(decay))
        )

    return do('Echo: Delay="{}" Decay="{}"'.format(delay, decay))


def fade_in() -> str:
    """TODO

    Audacity Documentation: Applies a linear fade-in to the selected audio - the rapidity of the fade-in depends entirely on the length of the selection it is applied to. For a more customizable logarithmic fade, use the Envelope Tool on the Tools Toolbar.
    """

    return do("FadeIn")


def fade_out() -> str:
    """TODO

    Audacity Documentation: Applies a linear fade-out to the selected audio - the rapidity of the fade-out depends entirely on the length of the selection it is applied to. For a more customizable logarithmic fade, use the Envelope Tool on the Tools Toolbar.
    """

    return do("FadeOut")


def invert() -> str:
    """TODO

    Audacity Documentation: This effect flips the audio samples upside-down. This normally does not affect the sound of the audio at all. It is occasionally useful for vocal removal.
    """

    return do("Invert")


def loudness_normalization(
    stereo_independent = False,
    LUFS_level: float = -23.0,
    RMS_level: float = -20.0,
    dual_mono = True,
    normalize_to = 0,
) -> str: # bool, float, float, bool, int
    """TODO

    Audacity Documentation: Changes the perceived loudness of the audio."""

    if not isinstance(stereo_independent, bool):
        raise PyAudacityException(
            "stereo_independent argument must be a bool, not"
            + str(type(stereo_independent))
        )
    if not isinstance(LUFS_level, (float, int)):
        raise PyAudacityException(
            "LUFS_level argument must be float or int, not " + str(type(LUFS_level))
        )
    if not isinstance(RMS_level, (float, int)):
        raise PyAudacityException(
            "RMS_level argument must be float or int, not " + str(type(RMS_level))
        )
    if not isinstance(dual_mono, bool):
        raise PyAudacityException(
            "dual_mono argument must be a bool, not" + str(type(dual_mono))
        )
    if not isinstance(normalize_to, int):
        raise PyAudacityException(
            "normalize_to argument must be int, not " + str(type(normalize_to))
        )

    return do(
        'LoudnessNormalization: StereoIndependent="{}" LUFSLevel="{}" RMFSLevel="{}" DualMono="{}" NormalizeTo="{}"'.format(
            stereo_independent, LUFS_level, RMS_level, dual_mono, normalize_to
        )
    )


# The documentation says this effect is not available for scripting.
# def noise_reduction():
#    # type: () -> str
#    """TODO
#
#    Audacity Documentation: This effect is ideal for reducing constant background noise such as fans, tape noise, or hums. It will not work very well for removing talking or music in the background. More details here
#    This effect is not currently available from scripting."""
#    return do('NoiseReduction')


def normalize(
    peak_level: float = -1.0, apply_gain = True, remove_dc_offset = True, stereo_independent = False
) -> str: # float, bool, bool, bool
    """TODO

    Audacity Documentation: Use the Normalize effect to set the maximum amplitude of a track, equalize the amplitudes of the left and right channels of a stereo track and optionally remove any DC offset from the track.
    """

    if not isinstance(peak_level, (float, int)):
        raise PyAudacityException(
            "peak_level argument must be float or int, not " + str(type(peak_level))
        )
    if not isinstance(apply_gain, bool):
        raise PyAudacityException(
            "apply_gain argument must be a bool, not" + str(type(apply_gain))
        )
    if not isinstance(remove_dc_offset, bool):
        raise PyAudacityException(
            "remove_dc_offset argument must be a bool, not"
            + str(type(remove_dc_offset))
        )
    if not isinstance(stereo_independent, bool):
        raise PyAudacityException(
            "stereo_independent argument must be a bool, not"
            + str(type(stereo_independent))
        )

    return do(
        'Normalize: PeakLevel="{}" ApplyGain="{}" RemoveDcOffset="{}" StereoIndependent="{}"'.format(
            peak_level, apply_gain, remove_dc_offset, stereo_independent
        )
    )


def paulstretch(stretch_factor = 10.0, time_resolution: float = 0.25) -> str: # float, float
    """TODO

    Audacity Documentation: Use Paulstretch only for an extreme time-stretch or "stasis" effect, This may be useful for synthesizer pad sounds, identifying performance glitches or just creating interesting aural textures. Use Change Tempo or Sliding Time Scale rather than Paulstretch for tasks like slowing down a song to a "practice" tempo.
    """

    if not isinstance(stretch_factor, (float, int)):
        raise PyAudacityException(
            "stretch_factor argument must be float or int, not "
            + str(type(stretch_factor))
        )
    if not isinstance(time_resolution, (float, int)):
        raise PyAudacityException(
            "time_resolution argument must be float or int, not "
            + str(type(time_resolution))
        )

    # TODO - documentation uses "Time Resolution" with a space. Check this out. I assume that there is no space for now.
    return do(
        'Paulstretch: StretchFactor="{}" TimeResolution="{}"'.format(
            stretch_factor, time_resolution
        )
    )


def phaser(
    stages = 2, dry_wet = 128, frequency: float = 0.4, phase: float = 0.0, depth = 100, feedback = 0, gain: float = -6.0
) -> str: # int, int, float, float, int, int, float
    """TODO

    Audacity Documentation: The name "Phaser" comes from "Phase Shifter", because it works by combining phase-shifted signals with the original signal. The movement of the phase-shifted signals is controlled using a Low Frequency Oscillator (LFO).
    """

    if not isinstance(stages, int):
        raise PyAudacityException(
            "stages argument must be int, not " + str(type(stages))
        )
    if not isinstance(dry_wet, int):
        raise PyAudacityException(
            "dry_wet argument must be int, not " + str(type(dry_wet))
        )
    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(phase, (float, int)):
        raise PyAudacityException(
            "phase argument must be float or int, not " + str(type(phase))
        )
    if not isinstance(depth, int):
        raise PyAudacityException("depth argument must be int, not " + str(type(depth)))
    if not isinstance(feedback, int):
        raise PyAudacityException(
            "feedback argument must be int, not " + str(type(feedback))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do(
        'Phaser: Stages="{}" DryWet="{}" Freq="{}" Phase="{}" Depth="{}" Feedback="{}" Gain="{}"'.format(
            stages, dry_wet, frequency, phase, depth, feedback, gain
        )
    )


def repair() -> str:
    """TODO

    Audacity Documentation: Fix one particular short click, pop or other glitch no more than 128 samples long.
    """

    return do("Repair")


def repeat(count = 1) -> str: # int
    """TODO

    Audacity Documentation: Repeats the selection the specified number of times."""

    if not isinstance(count, int):
        raise PyAudacityException("count argument must be int, not " + str(type(count)))

    return do('Repeat: Count="{}"'.format(count))


def reverb(
    room_size: float = 75.0,
    delay: float = 10.0,
    reverberance: float = 50.0,
    hf_damping: float = 50.0,
    tone_low: float = 100.0,
    tone_high: float = 100.0,
    wet_gain: float = -1.0,
    dry_gain: float = -1.0,
    stereo_width: float = 100.0,
    wet_only = False,
) -> str: # float, float, float, float, float, float, float, float, float, bool
    """TODO

    Audacity Documentation: A configurable stereo reverberation effect with built-in and user-added presets. It can be used to add ambience (an impression of the space in which a sound occurs) to a mono sound. Also use it to increase reverberation in stereo audio that sounds too "dry" or "close".
    """

    if not isinstance(room_size, (float, int)):
        raise PyAudacityException(
            "room_size argument must be float or int, not " + str(type(room_size))
        )
    if not isinstance(delay, (float, int)):
        raise PyAudacityException(
            "delay argument must be float or int, not " + str(type(delay))
        )
    if not isinstance(reverberance, (float, int)):
        raise PyAudacityException(
            "reverberance argument must be float or int, not " + str(type(reverberance))
        )
    if not isinstance(hf_damping, (float, int)):
        raise PyAudacityException(
            "hf_damping argument must be float or int, not " + str(type(hf_damping))
        )
    if not isinstance(tone_low, (float, int)):
        raise PyAudacityException(
            "tone_low argument must be float or int, not " + str(type(tone_low))
        )
    if not isinstance(tone_high, (float, int)):
        raise PyAudacityException(
            "tone_high argument must be float or int, not " + str(type(tone_high))
        )
    if not isinstance(wet_gain, (float, int)):
        raise PyAudacityException(
            "wet_gain argument must be float or int, not " + str(type(wet_gain))
        )
    if not isinstance(dry_gain, (float, int)):
        raise PyAudacityException(
            "dry_gain argument must be float or int, not " + str(type(dry_gain))
        )
    if not isinstance(stereo_width, (float, int)):
        raise PyAudacityException(
            "stereo_width argument must be float or int, not " + str(type(stereo_width))
        )
    if not isinstance(wet_only, bool):
        raise PyAudacityException(
            "wet_only argument must be a bool, not" + str(type(wet_only))
        )

    return do(
        'Reverb: RoomSize="{}" Delay="{}" Reverberance="{}" HfDamping="{}" ToneLow="{}" ToneHigh="{}" WetGain="{}" DryGain="{}" StereoWidth="{}" WetOnly="{}"'.format(
            room_size,
            delay,
            reverberance,
            hf_damping,
            tone_low,
            tone_high,
            wet_gain,
            dry_gain,
            stereo_width,
            wet_only,
        )
    )


def reverse() -> str:
    """TODO

    Audacity Documentation: Reverses the selected audio; after the effect the end of the audio will be heard first and the beginning last.
    """

    return do("Reverse")


def sliding_stretch(
    rate_percent_change_start: float = 0.0,
    rate_percent_change_end: float = 0.0,
    pitch_half_steps_start: float = 0.0,
    pitch_half_steps_end: float = 0.0,
    pitch_percent_change_start: float = 0.0,
    pitch_percent_change_end: float = 0.0,
) -> str: # float, float, float, float, float, float
    """TODO

    Audacity Documentation: This effect allows you to make a continuous change to the tempo and/or pitch of a selection by choosing initial and/or final change values.
    """

    if not isinstance(rate_percent_change_start, (float, int)):
        raise PyAudacityException(
            "rate_percent_change_start argument must be float or int, not "
            + str(type(rate_percent_change_start))
        )
    if not isinstance(rate_percent_change_end, (float, int)):
        raise PyAudacityException(
            "rate_percent_change_end argument must be float or int, not "
            + str(type(rate_percent_change_end))
        )
    if not isinstance(pitch_half_steps_start, (float, int)):
        raise PyAudacityException(
            "pitch_half_steps_start argument must be float or int, not "
            + str(type(pitch_half_steps_start))
        )
    if not isinstance(pitch_half_steps_end, (float, int)):
        raise PyAudacityException(
            "pitch_half_steps_end argument must be float or int, not "
            + str(type(pitch_half_steps_end))
        )
    if not isinstance(pitch_percent_change_start, (float, int)):
        raise PyAudacityException(
            "pitch_percent_change_start argument must be float or int, not "
            + str(type(pitch_percent_change_start))
        )
    if not isinstance(pitch_percent_change_end, (float, int)):
        raise PyAudacityException(
            "pitch_percent_change_end argument must be float or int, not "
            + str(type(pitch_percent_change_end))
        )

    return do(
        'TODO: RatePercentChangeStart="{}" RatePercentChangeEnd="{}" PitchHalfStepsStart="{}" PitchHalfStepsEnd="{}" PitchPercentChangeStart="{}" PitchPercentChangeEnd="{}"'
    ).format(
        rate_percent_change_start,
        rate_percent_change_end,
        pitch_half_steps_start,
        pitch_half_steps_end,
        pitch_percent_change_start,
        pitch_percent_change_end,
    )


def truncate_silence(
    threshold: float = -20.0,
    action="Truncate",
    minimum: float = 0.5,
    truncate: float = 0.5,
    compress: float = 50.0,
    independent = False,
) -> str: # float, str, float, float, float, bool
    """TODO

    Audacity Documentation: Automatically try to find and eliminate audible silences. Do not use this with faded audio.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    # TODO action check
    if not isinstance(minimum, (float, int)):
        raise PyAudacityException(
            "minimum argument must be float or int, not " + str(type(minimum))
        )
    if not isinstance(truncate, (float, int)):
        raise PyAudacityException(
            "truncate argument must be float or int, not " + str(type(truncate))
        )
    if not isinstance(compress, (float, int)):
        raise PyAudacityException(
            "compress argument must be float or int, not " + str(type(compress))
        )
    if not isinstance(independent, bool):
        raise PyAudacityException(
            "independent argument must be a bool, not" + str(type(independent))
        )

    return do(
        'TruncateSilence: Threshold="{}" Action="{}" Minimum="{}" Truncate="{}" Compress="{}" Independent="{}"'
    ).format(threshold, action, minimum, truncate, compress, independent)


def wahwah(freq = 1.5, phase: float = 0.0, depth = 70, resonance: float = 2.5, offset = 30, gain: float = -6.0) -> str: # float, float, int, float, int, float
    """TODO

    Audacity Documentation: Rapid tone quality variations, like that guitar sound so popular in the 1970's.
    """

    if not isinstance(freq, (float, int)):
        raise PyAudacityException(
            "freq argument must be float or int, not " + str(type(freq))
        )
    if not isinstance(phase, (float, int)):
        raise PyAudacityException(
            "phase argument must be float or int, not " + str(type(phase))
        )
    if not isinstance(depth, int):
        raise PyAudacityException("depth argument must be int, not " + str(type(depth)))
    if not isinstance(resonance, (float, int)):
        raise PyAudacityException(
            "resonance argument must be float or int, not " + str(type(resonance))
        )
    if not isinstance(offset, int):
        raise PyAudacityException(
            "offset argument must be int, not " + str(type(offset))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do(
        'Wahwah: Freq="{}" Phase="{}" Depth="{}" Resonance="{}" Offset="{}" Gain="{}"'
    ).format(freq, phase, depth, resonance, offset, gain)


def adjustable_fade(
        type: FadeType | str = FadeType.UP, 
        curve: float = 0.0, 
        units: FadeUnits | str = FadeUnits.PERCENT, 
        gain0 = 0, 
        gain1 = 0, 
        preset="None"
    ) -> str: # str, float, str, float, float, str
    """TODO

    Audacity Documentation: Enables you to control the shape of the fade (non-linear fading) to be applied by adjusting various parameters; allows partial (that is not from or to zero) fades up or down.
    """

    # TODO add param checks

    return do(
        'AdjustableFade: type="{}" curve="{}" units="{}" gain0="{}" gain1="{}" preset="{}"'.format(
            type, curve, units, gain0, gain1, preset
        )
    )


def clip_fix(threshold: float = 0.0, gain: float = 0.0) -> str: # float, float
    """TODO

    Audacity Documentation: Clip Fix attempts to reconstruct clipped regions by interpolating the lost signal.
    """

    if not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold argument must be float or int, not " + str(type(threshold))
        )
    if not isinstance(gain, (float, int)):
        raise PyAudacityException(
            "gain argument must be float or int, not " + str(type(gain))
        )

    return do('ClipFix: threshold="{}" gain="{}"'.format(threshold, gain))


def crossfade_clips() -> str:
    """TODO

    Audacity Documentation: Use Crossfade Clips to apply a simple crossfade to a selected pair of clips in a single audio track.
    """

    return do("CrossfadeClips")


def crossfade_tracks(type="ConstantGain", curve: float = 0.0, direction="Automatic") -> str: # str, float, str
    """TODO

    Audacity Documentation: Use Crossfade Tracks to make a smooth transition between two overlapping tracks one above the other. Place the track to be faded out above the track to be faded in then select the overlapping region in both tracks and apply the effect.
    """

    # TODO - add param checks
    return do(
        'CrossfadeTracks: type="{}" curve="{}" direction="{}"'.format(
            type, curve, direction
        )
    )


def delay(
    delay_type: DelayType | str = DelayType.REGULAR,
    d_gain: float = 0.0,
    delay: float = 0.0,
    pitch_type: str | PitchType = PitchType.PITCHTEMPO,
    shift: float = 0.0,
    number: int = 0,
    constrain: YesNo | str = YesNo.YES,
) -> str: # str, float, float, str, float, int, str
    """TODO

    Audacity Documentation: A configurable delay effect with variable delay time and pitch shifting of the delays.
    """

    # TODO - add param checks

    return do(
        'Delay: delay-type="{}" dgain="{}" delay="{}" pitch-type="{}" shift="{}" number="{}" constrain="{}"'.format(
            delay_type, d_gain, delay, pitch_type, shift, number, constrain
        )
    )


def high_pass_filter(frequency: float = 0.0, roll_off: str | Rolloff = Rolloff.DB6) -> str:
    """TODO

    Audacity Documentation: Passes frequencies above its cutoff frequency and attenuates frequencies below its cutoff frequency.
    """

    return do(
        'High-passFilter: frequency="{}" rolloff="{}"'.format(frequency, roll_off)
    )


def limiter(type="SoftLimit", gain_left = 0, gain_right = 0, limit = 0, hold = 0, makeup="No") -> str: # str, float, float, float, float, str
    """TODO

    Audacity Documentation: Limiter passes signals below a specified input level unaffected or gently reduced, while preventing the peaks of stronger signals from exceeding this threshold. Mastering engineers often use this type of dynamic range compression combined with make-up gain to increase the perceived loudness of an audio recording during the audio mastering process.
    """

    return do(
        'Limiter: type="{}" gain-L="{}" gain-R="{}" thresh="{}" hold="{}" makeup="{}"'.format(
            type, gain_left, gain_right, limit, hold, makeup
        )
    )


def low_pass_filter(frequency: float = 0.0, roll_off: str | Rolloff = Rolloff.DB6) -> str:
    """TODO

    Audacity Documentation: Passes frequencies below its cutoff frequency and attenuates frequencies above its cutoff frequency.
    """

    return do('Low-passFilter: frequency="{}" rolloff="{}"'.format(frequency, roll_off))


def notch_filter(frequency: float = 0.0, q: float = 0.0) -> str:
    """TODO

    Audacity Documentation: Greatly attenuate ("notch out"), a narrow frequency band. This is a good way to remove mains hum or a whistle confined to a specific frequency with minimal damage to the remainder of the audio.
    """

    if not isinstance(frequency, (float, int)):
        raise PyAudacityException(
            "frequency argument must be float or int, not " + str(type(frequency))
        )
    if not isinstance(q, (float, int)):
        raise PyAudacityException(
            "q argument must be float or int, not " + str(type(q))
        )

    return do('NotchFilter: frequency="{}" q="{}"').format(frequency, q)


def spectral_edit_multi_tool() -> str:
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view, applies a notch filter, high pass filter or low pass filter according to the spectral selection made. This effect can also be used to change the audio quality as an alternative to using Equalization.
    """
    return do("SpectralEditMultiTool")


def spectral_edit_parametric_eq(control_gain: float = 0.0) -> str:
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view and the spectral selection has a center frequency and an upper and lower boundary, performs the specified band cut or band boost. This can be used as an alternative to Equalization or may also be useful to repair damaged audio by reducing frequency spikes or boosting other frequencies to mask spikes.
    """

    if not isinstance(control_gain, (float, int)):
        raise PyAudacityException(
            "control_gain argument must be float or int, not " + str(type(control_gain))
        )

    # TODO - double check other macros for parameter names with dashes.
    return do('SpectralEditParametricEq: control-gain="{}"').format(control_gain)


def spectral_edit_shelves(control_gain: float = 0.0) -> str:
    """TODO

    Audacity Documentation: When the selected track is in spectrogram or spectrogram log(f) view, applies either a low- or high-frequency shelving filter or both filters, according to the spectral selection made. This can be used as an alternative to Equalization or may also be useful to repair damaged audio by reducing frequency spikes or boosting other frequencies to mask spikes.
    """

    if not isinstance(control_gain, (float, int)):
        raise PyAudacityException(
            "control_gain argument must be float or int, not " + str(type(control_gain))
        )

    return do('SpectralEditShelves: control-gain="{}"').format(control_gain)


def studio_fade_out() -> str:
    """TODO

    Audacity Documentation: Applies a more musical fade out to the selected audio, giving a more pleasing sounding result.
    """

    return do("StudioFadeOut")


def tremolo(wave: ToneWaveform | str = ToneWaveform.SINE, phase: int = 0, wet: int = 0, lfo: float = 0.0) -> str:
    """TODO

    Audacity Documentation: Modulates the volume of the selection at the depth and rate selected in the dialog. The same as the tremolo effect familiar to guitar and keyboard players.
    """

    # TODO check wave argument

    # TODO in the Tremolo dialog, wet's default is 40 and frequency's default is 4.0. Are the docs wrong?

    # TODO in the Tremolo dialog, lfo is labeled "Frequency". What's the correct name?

    if not isinstance(phase, int):
        raise PyAudacityException("phase argument must be int, not " + str(type(phase)))
    if not isinstance(wet, int):
        raise PyAudacityException("wet argument must be int, not " + str(type(wet)))
    if not isinstance(lfo, (float, int)):
        raise PyAudacityException(
            "lfo argument must be float or int, not " + str(type(lfo))
        )

    return do('Tremolo: wave="{}" phase="{}" wet="{}" lfo="{}"').format(
        wave, phase, wet, lfo
    )


def vocal_reduction_and_isolation(
    action="RemoveToMono", 
    strength: float = 0.0, 
    low_transition: float = 0.0,
    high_transition: float = 0.0
) -> str: # str, float, float, float
    """TODO

    Audacity Documentation: Attempts to remove or isolate center-panned audio from a stereo track. Most "Remove" options in this effect preserve the stereo image.
    """

    # TODO check action

    if not isinstance(strength, (float, int)):
        raise PyAudacityException(
            "strength argument must be float or int, not " + str(type(strength))
        )
    if not isinstance(low_transition, (float, int)):
        raise PyAudacityException(
            "low_transition argument must be float or int, not "
            + str(type(low_transition))
        )
    if not isinstance(high_transition, (float, int)):
        raise PyAudacityException(
            "high_transition argument must be float or int, not "
            + str(type(high_transition))
        )

    return do('TODO: strength="{}" low_transition="{}" high_transition="{}"').format(
        strength, low_transition, high_transition
    )


def vocoder(
    dst: float = 0.0,
    mst="BothChannels",
    bands: int = 0,
    track_vl: float = 0.0,
    noise_vl: float = 0.0,
    radar_vl: float = 0.0,
    radar_f: float = 0.0,
) -> str: # float, str, int, float, float, float, float
    """TODO

    Audacity Documentation: Synthesizes audio (usually a voice) in the left channel of a stereo track with a carrier wave (typically white noise) in the right channel to produce a modified version of the left channel. Vocoding a normal voice with white noise will produce a robot-like voice for special effects.
    """

    if not isinstance(dst, (float, int)):
        raise PyAudacityException(
            "dst argument must be float or int, not " + str(type(dst))
        )
    # TODO check mst
    if not isinstance(bands, int):
        raise PyAudacityException("bands argument must be int, not " + str(type(bands)))
    if not isinstance(track_vl, (float, int)):
        raise PyAudacityException(
            "track_vl argument must be float or int, not " + str(type(track_vl))
        )
    if not isinstance(noise_vl, (float, int)):
        raise PyAudacityException(
            "noise_vl argument must be float or int, not " + str(type(noise_vl))
        )
    if not isinstance(radar_vl, (float, int)):
        raise PyAudacityException(
            "radar_vl argument must be float or int, not " + str(type(radar_vl))
        )
    if not isinstance(radar_f, (float, int)):
        raise PyAudacityException(
            "radar_f argument must be float or int, not " + str(type(radar_f))
        )

    return do(
        'TODO: dst="{}" mst="{}" bands="{}" track-vl="{}" noise-vl="{}" radar-vl="{}" radar-f="{}"'
    ).format(dst, mst, bands, track_vl, noise_vl, radar_vl, radar_f)


# NOTE THE SPELLING OF "ANALYZERS"
def manage_analyzers() -> str:
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """
    return do("ManageAnalyzers")


# NOTE THE SPELLING OF "ANALYSER"
def contrast_analyser() -> str:
    """TODO

    Audacity Documentation: Analyzes a single mono or stereo speech track to determine the average RMS difference in volume (contrast) between foreground speech and background music, audience noise or similar. The purpose is to determine if the speech will be intelligible to the hard of hearing.
    """
    return do("ConrastAnalyser")


def plot_spectrum() -> str:
    """TODO

    Audacity Documentation: Takes the selected audio (which is a set of sound pressure values at points in time) and converts it to a graph of frequencies against amplitudes.
    """
    return do("PlotSpectrum")


def find_clipping(duty_cycle_start = 3, duty_cycle_end = 3) -> str: # int, int
    """TODO

    Audacity Documentation: Displays runs of clipped samples in a Label Track, as a screen-reader accessible alternative to View > Show Clipping. A run must include at least one clipped sample, but may include unclipped samples too.
    """

    # TODO Parameter names in documentation have spaces, double check

    if not isinstance(duty_cycle_start, int):
        raise PyAudacityException(
            "duty_cycle_start argument must be int, not " + str(type(duty_cycle_start))
        )
    if not isinstance(duty_cycle_end, int):
        raise PyAudacityException(
            "duty_cycle_end argument must be int, not " + str(type(duty_cycle_end))
        )

    return do('FindClipping: DutyCycleStart="{}" DutyCycleEnd="{}"').format(
        duty_cycle_start, duty_cycle_end
    )


def beat_finder(thresval: int = 0) -> str:
    """TODO

    Audacity Documentation: Attempts to place labels at beats which are much louder than the surrounding audio. It's a fairly rough and ready tool, and will not necessarily work well on a typical modern pop music track with compressed dynamic range. If you do not get enough beats detected, try reducing the "Threshold Percentage" setting.
    """

    if not isinstance(thresval, int):
        raise PyAudacityException(
            "thresval argument must be int, not " + str(type(thresval))
        )

    return do('BeatFinder: thresval="{}"').format(thresval)


def label_sounds(
    thershold_level: float = -30.0,
    threshold_measurement="Peak level",
    min_silence_duration: float = 0.0,
    min_label_interval: float = 0.0,
    label_type="Point before sound",
    max_leading_silence: float = 0.0,
    max_trailing_silence: float = 0.0,
    label_text="Sound ##1",
) -> str: # float, str, float, float, str, float, float, str
    """TODO

    Audacity Documentation: Divides up a track by placing labels for areas of sound that are separated by silence.
    """

    return do(
        'LabelSounds: threshold="{}" measurement="{}" sil-dur="{}" snd-dur="{}" type="{}" pre-offset="{}" post-offset="{}" text="{}"'.format(
            thershold_level,
            threshold_measurement,
            min_silence_duration,
            min_label_interval,
            label_type,
            max_leading_silence,
            max_trailing_silence,
            label_text,
        )
    )


def manage_tools() -> str:
    """TODO

    Audacity Documentation: Selecting this option from the Effect Menu (or the Generate Menu or Analyze Menu) takes you to a dialog where you can enable or disable particular Effects, Generators and Analyzers in Audacity. Even if you do not add any third-party plugins, you can use this to make the Effect menu shorter or longer as required. For details see Plugin Manager.
    """

    return do("ManageTools")


def manage_macros() -> str:
    """TODO

    Audacity Documentation: Creates a new macro or edits an existing macro."""

    return do("ManageMacros")


def apply_macro() -> str:
    """TODO

    Audacity Documentation: Displays a menu with list of all your Macros. Selecting any of these Macros by clicking on it will cause that Macro to be applied to the current project.
    """

    # TODO - documentation shows "Apply Macro" as the name, with a space. I assume this is wrong and remove the space:
    return do("ApplyMacro")


def benchmark():
    """Opens the Tools > Run Benchmark dialog.

    Audacity Documentation: A tool for measuring the performance of one part of Audacity.
    """

    return do("Benchmark")


def nyquist_prompt(command: str = "", version: int = 3) -> str:
    """TODO

    Audacity Documentation: Brings up a dialog where you can enter Nyquist commands. Nyquist is a programming language for generating, processing and analyzing audio. For more information see Nyquist Plugins Reference.
    """

    if not isinstance(command, str):
        raise PyAudacityException(
            "command argument must be str, not " + str(type(command))
        )
    if not isinstance(version, int):
        raise PyAudacityException(
            "version argument must be int, not " + str(type(version))
        )

    return do('NyquistPrompt: Command="{}" Version="{}"').format(command, version)


def regular_interval_labels(
    mode="Both",
    total_num: int = 0,
    interval: float = 0.0,
    region: float = 0.0,
    adjust="No",
    label_text="",
    zeros="TextOnly",
    first_number = 0,
    verbose="Details",
) -> str: # str, int, float, float, str, str, str, int, str
    """TODO

    Audacity Documentation: Places labels in a long track so as to divide it into smaller, equally sized segments.
    """

    # TODO check mode, adjust, label_text, zeros, verbose
    if not isinstance(total_num, int):
        raise PyAudacityException(
            "total_num argument must be int, not " + str(type(total_num))
        )
    if not isinstance(interval, (float, int)):
        raise PyAudacityException(
            "interval argument must be float or int, not " + str(type(interval))
        )
    if not isinstance(region, (float, int)):
        raise PyAudacityException(
            "region argument must be float or int, not " + str(type(region))
        )
    if not isinstance(first_number, int):
        raise PyAudacityException(
            "first_number argument must be int, not " + str(type(first_number))
        )

    return do(
        'RegularIntervalLabels: mode="{}" totalnum="{}" interval="{}" region="{}" adjust="{}" labeltext="{}" zeros="{}" firstnum="{}" verbose="{}"'
    ).format(
        mode,
        total_num,
        interval,
        region,
        adjust,
        label_text,
        zeros,
        first_number,
        verbose,
    )


def sample_data_export(
    export_filename: Path | str,
    limit_output_to_first: int = 100,
    measurement_scale="dB",
    index_format="None",
    include_header_information="None",
    optional_header_text="",
    channel_layout_for_stereo="L-R on Same Line",
    show_messages="Yes",
) -> str: # Union[Path, str], int, str, str, str, str, str, str
    """TODO

    Audacity Documentation: Reads the values of successive samples from the selected audio and prints this data to a plain text, CSV or HTML file.
    """

    # TODO - check params

    return do(
        'SampleDataExport: number="{}" units="{}" filename="{}" fileformat="{}" header="{}" optext="{}" channel-layout="{}" messages="{}"'.format(
            limit_output_to_first,
            measurement_scale,
            export_filename,
            index_format,
            include_header_information,
            optional_header_text,
            channel_layout_for_stereo,
            show_messages,
        )
    )



def apply_macros_palette() -> str:
    """TODO

    Audacity Documentation: Displays a menu with list of all your Macros which can be applied to the current project or to audio files.
    """
    return do("ApplyMacrosPalette")


def macro_fade_ends() -> str:
    """TODO

    Audacity Documentation: Fades in the first second and fades out the last second of a track.
    """
    return do("Macro_FadeEnds")


def macro_mp3_conversion() -> str:
    """TODO

    Audacity Documentation: Converts MP3."""
    return do("Macro_MP3Conversion")


def full_screen_on_off() -> str:
    """TODO

    Audacity Documentation: Toggle full screen mode with no title bar."""
    return do("FullScreenOnOff")


def play() -> str:
    """TODO

    Audacity Documentation: Play (or stop) audio."""
    return do("Play")


def stop() -> str:
    """TODO

    Audacity Documentation: Stop audio."""
    return do("Stop")


def play_one_sec() -> str:
    """TODO

    Audacity Documentation: Plays for one second centered on the current mouse pointer position (not from the current cursor position). See this page for an example.
    """
    return do("PlayOneSec")


def play_to_selection() -> str:
    """TODO

    Audacity Documentation: Plays to or from the current mouse pointer position to or from the start or end of the selection, depending on the pointer position. See this page for more details.
    """
    return do("PlayToSelection")


def play_before_selection_start() -> str:
    """TODO

    Audacity Documentation: Plays a short period before the start of the selected audio, the period before shares the setting of the cut preview.
    """
    return do("PlayBeforeSelectionStart")


def play_after_selection_start() -> str:
    """TODO

    Audacity Documentation: Plays a short period after the start of the selected audio, the period after shares the setting of the cut preview.
    """
    return do("PlayAfterSelectionStart")


def play_before_selection_end() -> str:
    """TODO

    Audacity Documentation: Plays a short period before the end of the selected audio, the period before shares the setting of the cut preview.
    """
    return do("PlayBeforeSelectionEnd")


def play_after_selection_end() -> str:
    """TODO

    Audacity Documentation: Plays a short period after the end of the selected audio, the period after shares the setting of the cut preview.
    """
    return do("PlayAfterSelectionEnd")


def play_before_and_after_selection_start() -> str:
    """TODO

    Audacity Documentation: Plays a short period before and after the start of the selected audio, the periods before and after share the setting of the cut preview.
    """
    return do("PlayBeforeAndAfterSelectionStart")


def play_before_and_after_selection_end() -> str:
    """TODO

    Audacity Documentation: Plays a short period before and after the end of the selected audio, the periods before and after share the setting of the cut preview.
    """
    return do("PlayBeforeAndAfterSelectionEnd")


def play_cut_preview() -> str:
    """TODO

    Audacity Documentation: Plays audio excluding the selection."""
    return do("PlayCutPreview")


def select_tool() -> str:
    """TODO

    Audacity Documentation: Chooses Selection tool."""
    return do("SelectTool")


def envelope_tool() -> str:
    """TODO

    Audacity Documentation: Chooses Envelope tool."""
    return do("EnvelopeTool")


def draw_tool() -> str:
    """TODO

    Audacity Documentation: Chooses Draw tool."""
    return do("DrawTool")


def zoom_tool() -> str:
    """TODO

    Audacity Documentation: Chooses Zoom tool."""
    return do("ZoomTool")


def multi_tool() -> str:
    """TODO

    Audacity Documentation: Chooses the Multi-Tool."""
    return do("MultiTool")


def prev_tool() -> str:
    """TODO

    Audacity Documentation: Cycles backwards through the tools, starting from the currently selected tool:  # type: () -> str starting from Selection, it would navigate to Multi-tool to Time Shift to Zoom to Draw to Envelope to Selection.
    """
    return do("PrevTool")


def next_tool() -> str:
    """TODO

    Audacity Documentation: Cycles forwards through the tools, starting from the currently selected tool:  # type: () -> str starting from Selection, it would navigate to Envelope to Draw to Zoom to Time Shift to Multi-tool to Selection.
    """
    return do("NextTool")


def output_gain() -> str:
    """TODO

    Audacity Documentation: Displays the Playback Volume dialog. You can type a new value for the playback volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("OutputGain")


def output_gain_inc() -> str:
    """TODO

    Audacity Documentation: Each key press will increase the playback volume by 0.1."""
    return do("OutputGainInc")


def output_gain_dec() -> str:
    """TODO

    Audacity Documentation: Each key press will decrease the playback volume by 0.1."""
    return do("OutputGainDec")


def input_gain() -> str:
    """TODO

    Audacity Documentation: Displays the Recording Volume dialog. You can type a new value for the recording volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("InputGain")


def input_gain_inc() -> str:
    """TODO

    Audacity Documentation: Each key press will increase the recording volume by 0.1."""
    return do("InputGainInc")


def input_gain_dec() -> str:
    """TODO

    Audacity Documentation: Each key press will decrease the recording volume by 0.1."""
    return do("InputGainDec")


def delete_key() -> str:
    """TODO

    Audacity Documentation: Deletes the selection. When focus is in Selection Toolbar, BACKSPACE is not a shortcut but navigates back to the previous digit and sets it to zero.
    """
    return do("DeleteKey")


def delete_key2() -> str:
    """TODO

    Audacity Documentation: Deletes the selection."""
    return do("DeleteKey2")


def play_at_speed() -> str:
    """TODO

    Audacity Documentation: Play audio at a faster or slower speed."""
    return do("PlayAtSpeed")


def play_at_speed_looped() -> str:
    """TODO

    Audacity Documentation: Combines looped play and play at speed."""
    return do("PlayAtSpeedLooped")


def play_at_speed_cut_preview() -> str:
    """TODO

    Audacity Documentation: Combines cut preview and play at speed."""
    return do("PlayAtSpeedCutPreview")


def set_play_speed() -> str:
    """TODO

    Audacity Documentation: Displays the Playback Speed dialog. You can type a new value for the playback volume (between 0 and 1), or press Tab, then use the left and right arrow keys to adjust the slider.
    """
    return do("SetPlaySpeed")


def play_speed_inc() -> str:
    """TODO

    Audacity Documentation: Each key press will increase the playback speed by 0.1."""
    return do("PlaySpeedInc")


def play_speed_dec() -> str:
    """TODO

    Audacity Documentation: Each key press will decrease the playback speed by 0.1."""
    return do("PlaySpeedDec")


def move_to_prev_label() -> str:
    """TODO

    Audacity Documentation: Moves selection to the previous label."""
    return do("MoveToPrevLabel")


def move_to_next_label() -> str:
    """TODO

    Audacity Documentation: Moves selection to the next label."""
    return do("MoveToNextLabel")


def seek_left_short() -> str:
    """TODO

    Audacity Documentation: Skips the playback cursor back one second by default."""
    return do("SeekLeftShort")


def seek_right_short() -> str:
    """TODO

    Audacity Documentation: Skips the playback cursor forward one second by default."""
    return do("SeekRightShort")


def seek_left_long() -> str:
    """TODO

    Audacity Documentation: Skips the playback cursor back 15 seconds by default."""
    return do("SeekLeftLong")


def seek_right_long() -> str:
    """TODO

    Audacity Documentation: Skips the playback cursor forward 15 seconds by default."""
    return do("SeekRightLong")


def input_device() -> str:
    """TODO

    Audacity Documentation: Displays the Select recording Device dialog for choosing the recording device, but only if the "Recording Device" dropdown menu in Device Toolbar has entries for devices. Otherwise, an recording error message will be displayed.
    """
    return do("InputDevice")


def output_device() -> str:
    """TODO

    Audacity Documentation: Displays the Select Playback Device dialog for choosing the playback device, but only if the "Playback Device" dropdown menu in Device Toolbar has entries for devices. Otherwise, an error message will be displayed.
    """
    return do("OutputDevice")


def audio_host() -> str:
    """TODO

    Audacity Documentation: Displays the Select Audio Host dialog for choosing the particular interface with which Audacity communicates with your chosen playback and recording devices.
    """
    return do("AudioHost")


def input_channels() -> str:
    """TODO

    Audacity Documentation: Displays the Select Recording Channels dialog for choosing the number of channels to be recorded by the chosen recording device.
    """
    return do("InputChannels")


def snap_to_off() -> str:
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Off".
    """
    return do("SnapToOff")


def snap_to_nearest() -> str:
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Nearest".
    """
    return do("SnapToNearest")


def snap_to_prior() -> str:
    """TODO

    Audacity Documentation: Equivalent to setting the Snap To control in Selection Toolbar to "Prior".
    """
    return do("SnapToPrior")


def sel_start() -> str:
    """TODO

    Audacity Documentation: Select from cursor to start of track."""
    return do("SelStart")


def sel_end() -> str:
    """TODO

    Audacity Documentation: Select from cursor to end of track."""
    return do("SelEnd")


def sel_ext_left() -> str:
    """TODO

    Audacity Documentation: Increases the size of the selection by extending it to the left. The amount of increase is dependent on the zoom level. If there is no selection one is created starting at the cursor position.
    """
    return do("SelExtLeft")


def sel_ext_right() -> str:
    """TODO

    Audacity Documentation: Increases the size of the selection by extending it to the right. The amount of increase is dependent on the zoom level. If there is no selection one is created starting at the cursor position.
    """
    return do("SelExtRight")


def sel_set_ext_left() -> str:
    """TODO

    Audacity Documentation: Extend selection left a little (is this a duplicate?)."""
    return do("SelSetExtLeft")


def sel_set_ext_right() -> str:
    """TODO

    Audacity Documentation: Extend selection right a litlle (is this a duplicate?)."""
    return do("SelSetExtRight")


def sel_cntr_left() -> str:
    """TODO

    Audacity Documentation: Decreases the size of the selection by contracting it from the right. The amount of decrease is dependent on the zoom level. If there is no selection no action is taken.
    """
    return do("SelCntrLeft")


def sel_cntr_right() -> str:
    """TODO

    Audacity Documentation: Decreases the size of the selection by contracting it from the left. The amount of decrease is dependent on the zoom level. If there is no selection no action is taken.
    """
    return do("SelCntrRight")


def prev_frame() -> str:
    """TODO

    Audacity Documentation: Move backward through currently focused toolbar in Upper Toolbar dock area, Track View and currently focused toolbar in Lower Toolbar dock area. Each use moves the keyboard focus as indicated.
    """
    return do("PrevFrame")


def next_frame() -> str:
    """TODO

    Audacity Documentation: Move forward through currently focused toolbar in Upper Toolbar dock area, Track View and currently focused toolbar in Lower Toolbar dock area. Each use moves the keyboard focus as indicated.
    """
    return do("NextFrame")


def prev_track() -> str:
    """TODO

    Audacity Documentation: Focus one track up."""
    return do("PrevTrack")


def next_track() -> str:
    """TODO

    Audacity Documentation: Focus one track down."""
    return do("NextTrack")


def first_track() -> str:
    """TODO

    Audacity Documentation: Focus on first track."""
    return do("FirstTrack")


def last_track() -> str:
    """TODO

    Audacity Documentation: Focus on last track."""
    return do("LastTrack")


def shift_up() -> str:
    """TODO

    Audacity Documentation: Focus one track up and select it."""
    return do("ShiftUp")


def shift_down() -> str:
    """TODO

    Audacity Documentation: Focus one track down and select it."""
    return do("ShiftDown")


def toggle() -> str:
    """TODO

    Audacity Documentation: Toggle focus on current track."""
    return do("Toggle")


def toggle_alt() -> str:
    """TODO

    Audacity Documentation: Toggle focus on current track."""
    return do("ToggleAlt")


def cursor_left() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one screen pixel to left. When a Snap To option is chosen, moves the cursor to the preceding unit of time as determined by the current selection format. If the key is held down, the cursor speed depends on the length of the tracks. When playing audio, moves the playback cursor as described at "Cursor Short Jump Left".
    """
    return do("CursorLeft")


def cursor_right() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one screen pixel to right. When a Snap To option is chosen, moves the cursor to the following unit of time as determined by the current selection format. If the key is held down, the cursor speed depends on the length of the tracks. When playing audio, moves the playback cursor as described at "Cursor Short Jump Right".
    """
    return do("CursorRight")


def cursor_short_jump_left() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one second left by default. When playing audio, moves the playback cursor one second left by default. The default value can be changed by adjusting the "Short Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorShortJumpLeft")


def cursor_short_jump_right() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor one second right by default. When playing audio, moves the playback cursor one second right by default. The default value can be changed by adjusting the "Short Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorShortJumpRight")


def cursor_long_jump_left() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor 15 seconds left by default. When playing audio, moves the playback cursor 15 seconds left by default. The default value can be changed by adjusting the "Long Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorLongJumpLeft")


def cursor_long_jump_right() -> str:
    """TODO

    Audacity Documentation: When not playing audio, moves the editing cursor 15 seconds right by default. When playing audio, moves the playback cursor 15 seconds right by default. The default value can be changed by adjusting the "Long Period" under "Seek Time when playing" in Playback Preferences.
    """
    return do("CursorLongJumpRight")


def clip_left() -> str:
    """TODO

    Audacity Documentation: Moves the currently focused audio track (or a separate clip in that track which contains the editing cursor or selection region) one screen pixel to left.
    """
    return do("ClipLeft")


def clip_right() -> str:
    """TODO

    Audacity Documentation: Moves the currently focused audio track (or a separate clip in that track which contains the editing cursor or selection region) one screen pixel to right.
    """
    return do("ClipRight")


def track_pan() -> str:
    """TODO

    Audacity Documentation: Brings up the Pan dialog for the focused track where you can enter a pan value, or use the slider for finer control of panning than is available when using the track pan slider.
    """
    return do("TrackPan")


def track_pan_left() -> str:
    """TODO

    Audacity Documentation: Controls the pan slider on the focused track. Each keypress changes the pan value by 10% left.
    """
    return do("TrackPanLeft")


def track_pan_right() -> str:
    """TODO

    Audacity Documentation: Controls the pan slider on the focused track. Each keypress changes the pan value by 10% right.
    """
    return do("TrackPanRight")


def track_gain() -> str:
    """TODO

    Audacity Documentation: Brings up the Gain dialog for the focused track where you can enter a gain value, or use the slider for finer control of gain than is available when using the track pan slider.
    """
    return do("TrackGain")


def track_gain_inc() -> str:
    """TODO

    Audacity Documentation: Controls the gain slider on the focused track. Each keypress increases the gain value by 1 dB.
    """
    return do("TrackGainInc")


def track_gain_dec() -> str:
    """TODO

    Audacity Documentation: Controls the gain slider on the focused track. Each keypress decreases the gain value by 1 dB.
    """
    return do("TrackGainDec")


def track_menu() -> str:
    """TODO

    Audacity Documentation: Opens the Audio Track Dropdown Menu on the focused audio track or other track type. In the audio track dropdown, use Up, and Down, arrow keys to navigate the menu and Enter, to select a menu item. Use Right, arrow to open the "Set Sample Format" and "Set Rate" choices or Left, arrow to leave those choices.
    """
    return do("TrackMenu")


def track_mute() -> str:
    """TODO

    Audacity Documentation: Toggles the Mute button on the focused track."""
    return do("TrackMute")


def track_solo() -> str:
    """TODO

    Audacity Documentation: Toggles the Solo button on the focused track."""
    return do("TrackSolo")


def track_close() -> str:
    """TODO

    Audacity Documentation: Close (remove) the focused track only."""
    return do("TrackClose")


def track_move_up() -> str:
    """Moves the focused track up by one position and moves the focus there.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("TrackMoveUp")


def track_move_down() -> str:
    """Moves the focused track down by one position and moves the focus there.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("TrackMoveDown")


def track_move_top() -> str:
    """Moves the focused track to the top of the track list and moves the focus there.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("TrackMoveTop")


def track_move_bottom() -> str:
    """Moves the focused track to the bottom of the track list and moves the focus there.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("TrackMoveBottom")


def select_time(start: float | None = None, end: float | None = None, relative_to: str | None = None) -> str: # Optional[float], Optional[float], Optional[str]
    """Modifies the temporal selection in the project.

    Parameters:
        start (float, optional): The start time of the selection in seconds.
        end (float, optional): The end time of the selection in seconds.
        relative_to (str, optional): Reference point for the selection ('ProjectStart', 'ProjectEnd', 'Cursor', etc.).

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If the arguments are of incorrect types.
    """
    if not isinstance(start, (type(None), float, int)):
        raise PyAudacityException(
            "start argument must be float or int, not " + str(type(start))
        )
    if not isinstance(end, (type(None), float, int)):
        raise PyAudacityException(
            "end argument must be float or int, not " + str(type(end))
        )
    if not isinstance(relative_to, (type(None), str)):
        raise PyAudacityException(
            "relative_to argument must be str, not " + str(type(relative_to))
        )

    # Only include arguments if they are not None
    macro_arguments = []
    if start is not None:
        macro_arguments.append('Start="{}"'.format(start))
    if end is not None:
        macro_arguments.append('End="{}"'.format(end))
    if relative_to is not None:
        macro_arguments.append('RelativeTo="{}"'.format(relative_to))

    return do("SelectTime: " + " ".join(macro_arguments))


def select_frequencies(high: float | None = None, low: float | None  = None) -> str:
    """Modifies the frequency selection range for spectral selection.

    Parameters:
        high (float, optional): The upper frequency limit in Hz.
        low (float, optional): The lower frequency limit in Hz.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If the arguments are of incorrect types.
    """
    if not isinstance(high, (type(None), float, int)):
        raise PyAudacityException(
            "high argument must be float or int, not " + str(type(high))
        )
    if not isinstance(low, (type(None), float, int)):
        raise PyAudacityException(
            "low argument must be float or int, not " + str(type(low))
        )

    # Only include arguments if they are not None
    macro_arguments = []
    if high is not None:
        macro_arguments.append('High="{}"'.format(high))
    if low is not None:
        macro_arguments.append('Low="{}"'.format(low))

    return do("SelectFrequencies: " + " ".join(macro_arguments))


def select_tracks(first = None, last = None, track = None, mode = None, track_count = None) -> str: # Optional[int], Optional[int], Optional[int], Optional[str], Optional[int]
    """Modifies which tracks are selected in the project.

    Parameters:
        first (int, optional): The first track number to select.
        last (int, optional): The last track number to select.
        track (int, optional): A specific track number to select.
        mode (str, optional): Selection mode ('Set', 'Add', 'Remove', 'Invert', 'Union').
        track_count (int, optional): Number of tracks to select starting from 'First'.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If the arguments are of incorrect types.
    """
    if not isinstance(first, (type(None), int)):
        raise PyAudacityException("first argument must be int, not " + str(type(first)))
    if not isinstance(last, (type(None), int)):
        raise PyAudacityException("last argument must be int, not " + str(type(last)))
    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track argument must be int, not " + str(type(track)))
    if not isinstance(mode, (type(None), str)):
        raise PyAudacityException("mode argument must be str, not " + str(type(mode)))
    if not isinstance(track_count, (type(None), int)):
        raise PyAudacityException(
            "track_count argument must be int, not " + str(type(track_count))
        )

    macro_arguments = []
    if first is not None:
        macro_arguments.append('First="{}"'.format(first))
    if last is not None:
        macro_arguments.append('Last="{}"'.format(last))
    if track is not None:
        macro_arguments.append('Track="{}"'.format(track))
    if mode is not None:
        macro_arguments.append('Mode="{}"'.format(mode))
    if track_count is not None:
        macro_arguments.append('TrackCount="{}"'.format(track_count))

    return do("SelectTracks: " + " ".join(macro_arguments))


def set_track_status(track = None, channel = None, name = None, selected = None, focused = None) -> str: # Optional[int], Optional[int], Optional[str], Optional[bool], Optional[bool]
    """Sets properties for a track or channel, such as selection and focus status.

    Parameters:
        track (int, optional): The track number to modify.
        channel (int, optional): The channel number within the track to modify.
        name (str, optional): The new name for the track.
        selected (bool, optional): Whether the track is selected.
        focused (bool, optional): Whether the track is focused.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If the arguments are of incorrect types.
    """
    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track argument must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException(
            "channel argument must be int, not " + str(type(channel))
        )
    if not isinstance(name, (type(None), str)):
        raise PyAudacityException("name argument must be str, not " + str(type(name)))
    if not isinstance(selected, (type(None), bool)):
        raise PyAudacityException(
            "selected argument must be bool, not " + str(type(selected))
        )
    if not isinstance(focused, (type(None), bool)):
        raise PyAudacityException(
            "focused argument must be bool, not " + str(type(focused))
        )

    macro_arguments = []
    if track is not None:
        macro_arguments.append('Track="{}"'.format(track))
    if channel is not None:
        macro_arguments.append('Channel="{}"'.format(channel))
    if name is not None:
        macro_arguments.append('Name="{}"'.format(name))
    if selected is not None:
        macro_arguments.append('Selected="{}"'.format("1" if selected else "0"))
    if focused is not None:
        macro_arguments.append('Focused="{}"'.format("1" if focused else "0"))

    return do("SetTrackStatus: " + " ".join(macro_arguments))


def set_track_audio(
    track: int | None = None,
    channel: int | None  = None,
    pan: float | None  = None,
    gain: float | None  = None,
    mute: bool | None = None,
    solo: bool | None  = None
) -> str:
    """Sets audio properties for a track or channel, such as pan, gain, mute, and solo status.

    Parameters:
        track (int, optional): The track number to modify.
        channel (int, optional): The channel number within the track to modify.
        pan (float, optional): The pan setting (-1.0 for full left, 1.0 for full right).
        gain (float, optional): The gain setting in dB (-36.0 to +36.0).
        mute (bool, optional): Whether the track is muted.
        solo (bool, optional): Whether the track is soloed.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If the arguments are of incorrect types.
    """
    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track argument must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException(
            "channel argument must be int, not " + str(type(channel))
        )
    if not isinstance(pan, (type(None), float, int)):
        raise PyAudacityException("pan argument must be float, not " + str(type(pan)))
    if not isinstance(gain, (type(None), float, int)):
        raise PyAudacityException("gain argument must be float, not " + str(type(gain)))
    if not isinstance(mute, (type(None), bool)):
        raise PyAudacityException("mute argument must be bool, not " + str(type(mute)))
    if not isinstance(solo, (type(None), bool)):
        raise PyAudacityException("solo argument must be bool, not " + str(type(solo)))

    macro_arguments = []
    if track is not None:
        macro_arguments.append('Track="{}"'.format(track))
    if channel is not None:
        macro_arguments.append('Channel="{}"'.format(channel))
    if pan is not None:
        macro_arguments.append('Pan="{}"'.format(pan))
    if gain is not None:
        macro_arguments.append('Gain="{}"'.format(gain))
    if mute is not None:
        macro_arguments.append('Mute="{}"'.format("1" if mute else "0"))
    if solo is not None:
        macro_arguments.append('Solo="{}"'.format("1" if solo else "0"))

    return do("SetTrackAudio: " + " ".join(macro_arguments))


def set_track_visuals(
    track = None,
    channel = None,
    height = None,
    display = None,
    scale = None,
    color = None,
    vzoom = None,
    vzoomhigh = None,
    vzoomlow = None,
    specprefs = None,
    spectralsel = None,
    scheme = None,
) -> str: # Optional[int], Optional[int], Optional[int], Optional[str], Optional[str], Optional[str], Optional[str], Optional[float], Optional[float], Optional[bool], Optional[bool], Optional[str]
    """Sets visual properties for a track or channel.

    Parameters:
        track (int, optional): The track number to modify.
        channel (int, optional): The channel number within the track to modify.
        height (int, optional): The height of the track in pixels.
        display (str, optional): Display mode ('Waveform', 'Spectrogram', 'Multi-view').
        scale (str, optional): Scale mode ('Linear', 'dB').
        color (str, optional): Color scheme ('Color0', 'Color1', 'Color2', 'Color3').
        vzoom (str, optional): Vertical zoom mode ('Reset', 'Times2', 'HalfWave').
        vzoomhigh (float, optional): Upper limit of vertical zoom.
        vzoomlow (float, optional): Lower limit of vertical zoom.
        specprefs (bool, optional): Use general spectral preferences if True.
        spectralsel (bool, optional): Enable spectral selection if True.
        scheme (str, optional): Color scheme ('Color (default)', 'Color (classic)', 'Grayscale', 'Inverse Grayscale').

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If any of the arguments are of incorrect types or invalid values.
    """
    valid_displays = ["Waveform", "Spectrogram", "Multi-view"]
    valid_scales = ["Linear", "dB"]
    valid_colors = ["Color0", "Color1", "Color2", "Color3"]
    valid_vzooms = ["Reset", "Times2", "HalfWave"]
    valid_schemes = [
        "Color (default)",
        "Color (classic)",
        "Grayscale",
        "Inverse Grayscale",
    ]

    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException("channel must be int, not " + str(type(channel)))
    if not isinstance(height, (type(None), int)):
        raise PyAudacityException("height must be int, not " + str(type(height)))
    if display is not None and display not in valid_displays:
        raise PyAudacityException(
            f"display must be one of {valid_displays}, not {display}"
        )
    if scale is not None and scale not in valid_scales:
        raise PyAudacityException(f"scale must be one of {valid_scales}, not {scale}")
    if color is not None and color not in valid_colors:
        raise PyAudacityException(f"color must be one of {valid_colors}, not {color}")
    if vzoom is not None and vzoom not in valid_vzooms:
        raise PyAudacityException(f"vzoom must be one of {valid_vzooms}, not {vzoom}")
    if not isinstance(vzoomhigh, (type(None), float, int)):
        raise PyAudacityException(
            "vzoomhigh must be float or int, not " + str(type(vzoomhigh))
        )
    if not isinstance(vzoomlow, (type(None), float, int)):
        raise PyAudacityException(
            "vzoomlow must be float or int, not " + str(type(vzoomlow))
        )
    if not isinstance(specprefs, (type(None), bool)):
        raise PyAudacityException("specprefs must be bool, not " + str(type(specprefs)))
    if not isinstance(spectralsel, (type(None), bool)):
        raise PyAudacityException(
            "spectralsel must be bool, not " + str(type(spectralsel))
        )
    if scheme is not None and scheme not in valid_schemes:
        raise PyAudacityException(
            f"scheme must be one of {valid_schemes}, not {scheme}"
        )

    macro_arguments = []
    if track is not None:
        macro_arguments.append(f'Track="{track}"')
    if channel is not None:
        macro_arguments.append(f'Channel="{channel}"')
    if height is not None:
        macro_arguments.append(f'Height="{height}"')
    if display is not None:
        macro_arguments.append(f'Display="{display}"')
    if scale is not None:
        macro_arguments.append(f'Scale="{scale}"')
    if color is not None:
        macro_arguments.append(f'Color="{color}"')
    if vzoom is not None:
        macro_arguments.append(f'VZoom="{vzoom}"')
    if vzoomhigh is not None:
        macro_arguments.append(f'VZoomHigh="{vzoomhigh}"')
    if vzoomlow is not None:
        macro_arguments.append(f'VZoomLow="{vzoomlow}"')
    if specprefs is not None:
        macro_arguments.append(f'SpecPrefs="{int(specprefs)}"')
    if spectralsel is not None:
        macro_arguments.append(f'SpectralSel="{int(spectralsel)}"')
    if scheme is not None:
        macro_arguments.append(f'Scheme="{scheme}"')

    return do("SetTrackVisuals: " + " ".join(macro_arguments))


def get_preference(name) -> str: # str
    """Gets the value of a single preference setting.

    Parameters:
        name (str): The name of the preference setting to retrieve.

    Returns:
        str: The value of the preference setting.

    Raises:
        PyAudacityException: If the name is not a string.
    """
    if not isinstance(name, str):
        raise PyAudacityException("name must be str, not " + str(type(name)))

    return do(f'GetPreference: Name="{name}"')


def set_preference(name, value, reload = False) -> str: # str, str, bool
    """Sets a single preference setting.

    Parameters:
        name (str): The name of the preference setting to set.
        value (str): The value to set for the preference.
        reload (bool, optional): Whether to reload Audacity to apply the change.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types.
    """
    if not isinstance(name, str):
        raise PyAudacityException("name must be str, not " + str(type(name)))
    if not isinstance(value, str):
        raise PyAudacityException("value must be str, not " + str(type(value)))
    if not isinstance(reload, bool):
        raise PyAudacityException("reload must be bool, not " + str(type(reload)))

    reload_value = "1" if reload else "0"
    return do(f'SetPreference: Name="{name}" Value="{value}" Reload="{reload_value}"')


def set_clip(track = None, channel = None, at = None, color = None, start = None) -> str: # Optional[int], Optional[int], Optional[float], Optional[str], Optional[float]
    """Modifies a clip by specifying a time within it.

    Parameters:
        track (int, optional): The track number where the clip is located.
        channel (int, optional): The channel number within the track.
        at (float, optional): A time within the clip in seconds.
        color (str, optional): Color of the clip ('Color0', 'Color1', 'Color2', 'Color3').
        start (float, optional): The new start time of the clip in seconds.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or invalid values.
    """
    valid_colors = ["Color0", "Color1", "Color2", "Color3"]

    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException("channel must be int, not " + str(type(channel)))
    if not isinstance(at, (type(None), float, int)):
        raise PyAudacityException("at must be float or int, not " + str(type(at)))
    if color is not None and color not in valid_colors:
        raise PyAudacityException(f"color must be one of {valid_colors}, not {color}")
    if not isinstance(start, (type(None), float, int)):
        raise PyAudacityException("start must be float or int, not " + str(type(start)))

    macro_arguments = []
    if track is not None:
        macro_arguments.append(f'Track="{track}"')
    if channel is not None:
        macro_arguments.append(f'Channel="{channel}"')
    if at is not None:
        macro_arguments.append(f'At="{at}"')
    if color is not None:
        macro_arguments.append(f'Color="{color}"')
    if start is not None:
        macro_arguments.append(f'Start="{start}"')

    return do("SetClip: " + " ".join(macro_arguments))


def set_envelope(track = None, channel = None, time = None, value = None, delete = None) -> str: # Optional[int], Optional[int], Optional[float], Optional[float], Optional[bool]
    """Modifies an envelope by specifying a time within it.

    Parameters:
        track (int, optional): The track number where the envelope is located.
        channel (int, optional): The channel number within the track.
        time (float, optional): The time within the envelope in seconds.
        value (float, optional): The envelope value at the specified time.
        delete (bool, optional): If True, deletes the entire envelope.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types.
    """
    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException("channel must be int, not " + str(type(channel)))
    if not isinstance(time, (type(None), float, int)):
        raise PyAudacityException("time must be float or int, not " + str(type(time)))
    if not isinstance(value, (type(None), float, int)):
        raise PyAudacityException("value must be float or int, not " + str(type(value)))
    if not isinstance(delete, (type(None), bool)):
        raise PyAudacityException("delete must be bool, not " + str(type(delete)))

    macro_arguments = []
    if track is not None:
        macro_arguments.append(f'Track="{track}"')
    if channel is not None:
        macro_arguments.append(f'Channel="{channel}"')
    if time is not None:
        macro_arguments.append(f'Time="{time}"')
    if value is not None:
        macro_arguments.append(f'Value="{value}"')
    if delete is not None:
        macro_arguments.append(f'Delete="{int(delete)}"')

    return do("SetEnvelope: " + " ".join(macro_arguments))


def set_label(label, text = None, start = None, end = None, selected = None) -> str: # int, Optional[str], Optional[float], Optional[float], Optional[bool]
    """Modifies an existing label.

    Parameters:
        label (int): The label number to modify.
        text (str, optional): The new text for the label.
        start (float, optional): The new start time of the label in seconds.
        end (float, optional): The new end time of the label in seconds.
        selected (bool, optional): Whether the label is selected.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types.
    """
    if not isinstance(label, int):
        raise PyAudacityException("label must be int, not " + str(type(label)))
    if not isinstance(text, (type(None), str)):
        raise PyAudacityException("text must be str, not " + str(type(text)))
    if not isinstance(start, (type(None), float, int)):
        raise PyAudacityException("start must be float or int, not " + str(type(start)))
    if not isinstance(end, (type(None), float, int)):
        raise PyAudacityException("end must be float or int, not " + str(type(end)))
    if not isinstance(selected, (type(None), bool)):
        raise PyAudacityException("selected must be bool, not " + str(type(selected)))

    macro_arguments = [f'Label="{label}"']
    if text is not None:
        macro_arguments.append(f'Text="{text}"')
    if start is not None:
        macro_arguments.append(f'Start="{start}"')
    if end is not None:
        macro_arguments.append(f'End="{end}"')
    if selected is not None:
        macro_arguments.append(f'Selected="{int(selected)}"')

    return do("SetLabel: " + " ".join(macro_arguments))


def set_project(name = None, rate = None, x = None, y = None, width = None, height = None) -> str: # Optional[str], Optional[float], Optional[int], Optional[int], Optional[int], Optional[int]
    """Sets properties for the project window.

    Parameters:
        name (str, optional): The new caption for the project window.
        rate (float, optional): The new sample rate for the project.
        x (int, optional): The X position of the window.
        y (int, optional): The Y position of the window.
        width (int, optional): The width of the window.
        height (int, optional): The height of the window.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types.
    """
    if not isinstance(name, (type(None), str)):
        raise PyAudacityException("name must be str, not " + str(type(name)))
    if not isinstance(rate, (type(None), float, int)):
        raise PyAudacityException("rate must be float or int, not " + str(type(rate)))
    if not isinstance(x, (type(None), int)):
        raise PyAudacityException("x must be int, not " + str(type(x)))
    if not isinstance(y, (type(None), int)):
        raise PyAudacityException("y must be int, not " + str(type(y)))
    if not isinstance(width, (type(None), int)):
        raise PyAudacityException("width must be int, not " + str(type(width)))
    if not isinstance(height, (type(None), int)):
        raise PyAudacityException("height must be int, not " + str(type(height)))

    macro_arguments = []
    if name is not None:
        macro_arguments.append(f'Name="{name}"')
    if rate is not None:
        macro_arguments.append(f'Rate="{rate}"')
    if x is not None:
        macro_arguments.append(f'X="{x}"')
    if y is not None:
        macro_arguments.append(f'Y="{y}"')
    if width is not None:
        macro_arguments.append(f'Width="{width}"')
    if height is not None:
        macro_arguments.append(f'Height="{height}"')

    return do("SetProject: " + " ".join(macro_arguments))


def select(
    start = None,
    end = None,
    relative_to = None,
    high = None,
    low = None,
    track = None,
    track_count = None,
    mode = None,
) -> str: # Optional[float], Optional[float], Optional[str], Optional[float], Optional[float], Optional[int], Optional[int], Optional[str]
    """Selects audio in the project.

    Parameters:
        start (float, optional): The start time of the selection in seconds.
        end (float, optional): The end time of the selection in seconds.
        relative_to (str, optional): Reference point for the selection ('ProjectStart', 'Project', 'ProjectEnd', 'SelectionStart', 'Selection', 'SelectionEnd').
        high (float, optional): Upper frequency limit for spectral selection.
        low (float, optional): Lower frequency limit for spectral selection.
        track (int, optional): Track number to select.
        track_count (int, optional): Number of tracks to select starting from 'track'.
        mode (str, optional): Selection mode ('Set', 'Add', 'Remove').

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or invalid values.
    """
    valid_relative_to = [
        "ProjectStart",
        "Project",
        "ProjectEnd",
        "SelectionStart",
        "Selection",
        "SelectionEnd",
    ]
    valid_modes = ["Set", "Add", "Remove"]

    if not isinstance(start, (type(None), float, int)):
        raise PyAudacityException("start must be float or int, not " + str(type(start)))
    if not isinstance(end, (type(None), float, int)):
        raise PyAudacityException("end must be float or int, not " + str(type(end)))
    if relative_to is not None and relative_to not in valid_relative_to:
        raise PyAudacityException(
            f"relative_to must be one of {valid_relative_to}, not {relative_to}"
        )
    if not isinstance(high, (type(None), float, int)):
        raise PyAudacityException("high must be float or int, not " + str(type(high)))
    if not isinstance(low, (type(None), float, int)):
        raise PyAudacityException("low must be float or int, not " + str(type(low)))
    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track must be int, not " + str(type(track)))
    if not isinstance(track_count, (type(None), int)):
        raise PyAudacityException(
            "track_count must be int, not " + str(type(track_count))
        )
    if mode is not None and mode not in valid_modes:
        raise PyAudacityException(f"mode must be one of {valid_modes}, not {mode}")

    macro_arguments = []
    if start is not None:
        macro_arguments.append(f'Start="{start}"')
    if end is not None:
        macro_arguments.append(f'End="{end}"')
    if relative_to is not None:
        macro_arguments.append(f'RelativeTo="{relative_to}"')
    if high is not None:
        macro_arguments.append(f'High="{high}"')
    if low is not None:
        macro_arguments.append(f'Low="{low}"')
    if track is not None:
        macro_arguments.append(f'Track="{track}"')
    if track_count is not None:
        macro_arguments.append(f'TrackCount="{track_count}"')
    if mode is not None:
        macro_arguments.append(f'Mode="{mode}"')

    return do("Select: " + " ".join(macro_arguments))


def set_track(
    track = None,
    channel = None,
    name = None,
    selected = None,
    focused = None,
    mute = None,
    solo = None,
    gain = None,
    pan = None,
    height = None,
    display = None,
    scale = None,
    color = None,
    vzoom = None,
    vzoomhigh = None,
    vzoomlow = None,
    specprefs = None,
    spectralsel = None,
    grayscale = None,
) -> str: # Optional[int], Optional[int], Optional[str], Optional[bool], Optional[bool], Optional[bool], Optional[bool], Optional[float], Optional[float], Optional[int], Optional[str], Optional[str], Optional[str], Optional[str], Optional[float], Optional[float], Optional[bool], Optional[bool], Optional[bool]
    """Sets properties for a track or channel.

    Parameters:
        track (int, optional): The track number to modify.
        channel (int, optional): The channel number within the track.
        name (str, optional): The new name for the track.
        selected (bool, optional): Whether the track is selected.
        focused (bool, optional): Whether the track is focused.
        mute (bool, optional): Whether the track is muted.
        solo (bool, optional): Whether the track is soloed.
        gain (float, optional): The gain setting in dB (-36.0 to +36.0).
        pan (float, optional): The pan setting (-1.0 for full left, 1.0 for full right).
        height (int, optional): The height of the track in pixels.
        display (str, optional): Display mode ('Waveform', 'Spectrogram').
        scale (str, optional): Scale mode ('Linear', 'dB').
        color (str, optional): Color scheme ('Color0', 'Color1', 'Color2', 'Color3').
        vzoom (str, optional): Vertical zoom mode ('Reset', 'Times2', 'HalfWave').
        vzoomhigh (float, optional): Upper limit of vertical zoom.
        vzoomlow (float, optional): Lower limit of vertical zoom.
        specprefs (bool, optional): Use general spectral preferences if True.
        spectralsel (bool, optional): Enable spectral selection if True.
        grayscale (bool, optional): Use grayscale display if True.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or invalid values.
    """
    valid_displays = ["Waveform", "Spectrogram"]
    valid_scales = ["Linear", "dB"]
    valid_colors = ["Color0", "Color1", "Color2", "Color3"]
    valid_vzooms = ["Reset", "Times2", "HalfWave"]

    if not isinstance(track, (type(None), int)):
        raise PyAudacityException("track must be int, not " + str(type(track)))
    if not isinstance(channel, (type(None), int)):
        raise PyAudacityException("channel must be int, not " + str(type(channel)))
    if not isinstance(name, (type(None), str)):
        raise PyAudacityException("name must be str, not " + str(type(name)))
    if not isinstance(selected, (type(None), bool)):
        raise PyAudacityException("selected must be bool, not " + str(type(selected)))
    if not isinstance(focused, (type(None), bool)):
        raise PyAudacityException("focused must be bool, not " + str(type(focused)))
    if not isinstance(mute, (type(None), bool)):
        raise PyAudacityException("mute must be bool, not " + str(type(mute)))
    if not isinstance(solo, (type(None), bool)):
        raise PyAudacityException("solo must be bool, not " + str(type(solo)))
    if not isinstance(gain, (type(None), float, int)):
        raise PyAudacityException("gain must be float or int, not " + str(type(gain)))
    if not isinstance(pan, (type(None), float, int)):
        raise PyAudacityException("pan must be float or int, not " + str(type(pan)))
    if not isinstance(height, (type(None), int)):
        raise PyAudacityException("height must be int, not " + str(type(height)))
    if display is not None and display not in valid_displays:
        raise PyAudacityException(
            f"display must be one of {valid_displays}, not {display}"
        )
    if scale is not None and scale not in valid_scales:
        raise PyAudacityException(f"scale must be one of {valid_scales}, not {scale}")
    if color is not None and color not in valid_colors:
        raise PyAudacityException(f"color must be one of {valid_colors}, not {color}")
    if vzoom is not None and vzoom not in valid_vzooms:
        raise PyAudacityException(f"vzoom must be one of {valid_vzooms}, not {vzoom}")
    if not isinstance(vzoomhigh, (type(None), float, int)):
        raise PyAudacityException(
            "vzoomhigh must be float or int, not " + str(type(vzoomhigh))
        )
    if not isinstance(vzoomlow, (type(None), float, int)):
        raise PyAudacityException(
            "vzoomlow must be float or int, not " + str(type(vzoomlow))
        )
    if not isinstance(specprefs, (type(None), bool)):
        raise PyAudacityException("specprefs must be bool, not " + str(type(specprefs)))
    if not isinstance(spectralsel, (type(None), bool)):
        raise PyAudacityException(
            "spectralsel must be bool, not " + str(type(spectralsel))
        )
    if not isinstance(grayscale, (type(None), bool)):
        raise PyAudacityException("grayscale must be bool, not " + str(type(grayscale)))

    macro_arguments = []
    if track is not None:
        macro_arguments.append(f'Track="{track}"')
    if channel is not None:
        macro_arguments.append(f'Channel="{channel}"')
    if name is not None:
        macro_arguments.append(f'Name="{name}"')
    if selected is not None:
        macro_arguments.append(f'Selected="{int(selected)}"')
    if focused is not None:
        macro_arguments.append(f'Focused="{int(focused)}"')
    if mute is not None:
        macro_arguments.append(f'Mute="{int(mute)}"')
    if solo is not None:
        macro_arguments.append(f'Solo="{int(solo)}"')
    if gain is not None:
        macro_arguments.append(f'Gain="{gain}"')
    if pan is not None:
        macro_arguments.append(f'Pan="{pan}"')
    if height is not None:
        macro_arguments.append(f'Height="{height}"')
    if display is not None:
        macro_arguments.append(f'Display="{display}"')
    if scale is not None:
        macro_arguments.append(f'Scale="{scale}"')
    if color is not None:
        macro_arguments.append(f'Color="{color}"')
    if vzoom is not None:
        macro_arguments.append(f'VZoom="{vzoom}"')
    if vzoomhigh is not None:
        macro_arguments.append(f'VZoomHigh="{vzoomhigh}"')
    if vzoomlow is not None:
        macro_arguments.append(f'VZoomLow="{vzoomlow}"')
    if specprefs is not None:
        macro_arguments.append(f'SpecPrefs="{int(specprefs)}"')
    if spectralsel is not None:
        macro_arguments.append(f'SpectralSel="{int(spectralsel)}"')
    if grayscale is not None:
        macro_arguments.append(f'GrayScale="{int(grayscale)}"')

    return do("SetTrack: " + " ".join(macro_arguments))


def get_info(type="Commands", format="JSON") -> str: # str, str
    """TODO

    Audacity Documentation: Gets information in a list in one of three formats."""

    if type.title() not in (
        "Commands",
        "Menus",
        "Preferences",
        "Tracks",
        "Clips",
        "Envelopes",
        "Labels",
        "Boxes",
    ):
        raise PyAudacityException(
            'type argument must be one of "Commands", "Menus", "Preferences", "Tracks", "Clips", "Envelopes", "Labels", or "Boxes"'
        )
    if format.title() not in ("JSON", "LISP", "Brief"):
        raise PyAudacityException(
            'format argument must be one of "JSON", "LISP", or "Brief"'
        )

    return do('GetInfo: Type="{}" Format="{}"'.format(type, format))


def message(text="Some message") -> str: # str
    """TODO

    Audacity Documentation: Used in testing. Sends the Text string back to you."""

    if not isinstance(text, str):
        raise PyAudacityException(
            "message argument must be str, not " + str(type(text))
        )

    return do('Message: Text="{}"'.format(text))



def dtmf_tones(DTMF_sequence="audacity", tone_silence_ratio: float = 0.55, amplitude: float = 0.8) -> str: # str, float, float
    """Generates dual-tone multi-frequency (DTMF) tones like those produced by telephone keypads.

    **Note:** As per your observation, the `DutyCycle` parameter seems to have no effect.
    Audacity's UI specifies "Tone/Silence Ratio" instead of "Duty Cycle". We'll use
    `tone_silence_ratio` to reflect this.

    Parameters:
        DTMF_sequence (str, optional): The sequence of characters to generate tones for.
        tone_silence_ratio (float, optional): The ratio of tone duration to silence duration.
            Must be between 0 and 1.
        amplitude (float, optional): The amplitude of the generated tones (0.0 to 1.0).

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    if not isinstance(DTMF_sequence, str):
        raise PyAudacityException(
            "DTMF_sequence must be a str, not " + str(type(DTMF_sequence))
        )
    if not isinstance(tone_silence_ratio, (float, int)):
        raise PyAudacityException(
            "tone_silence_ratio must be float or int, not "
            + str(type(tone_silence_ratio))
        )
    if not 0 <= tone_silence_ratio <= 1:
        raise PyAudacityException(
            "tone_silence_ratio must be between 0 and 1, got " + str(tone_silence_ratio)
        )
    if not isinstance(amplitude, (float, int)):
        raise PyAudacityException(
            "amplitude must be float or int, not " + str(type(amplitude))
        )
    if not 0.0 <= amplitude <= 1.0:
        raise PyAudacityException(
            "amplitude must be between 0.0 and 1.0, got " + str(amplitude)
        )

    # Build the command string
    command = (
        f'DtmfTones: Sequence="{DTMF_sequence}" '
        f'ToneSilenceRatio="{tone_silence_ratio}" Amplitude="{amplitude}"'
    )

    return do(command)


def distortion(
    mode = None,
    drive = None,
    tone = None,
    compensate = None,
    blend = None,
    level = None,
    threshold = None,
    hardness = None,
    use_wave_shaper = None,
) -> str: # Optional[str], Optional[float], Optional[float], Optional[bool], Optional[float], Optional[float], Optional[float], Optional[float], Optional[bool]
    """Applies distortion effects to the selected audio.

    Parameters:
        mode (str, optional): The distortion mode to use (e.g., 'Soft Clipping', 'Hard Clipping').
        drive (float, optional): Amount of distortion drive.
        tone (float, optional): Adjusts the tone of the distortion.
        compensate (bool, optional): If True, compensates for volume changes.
        blend (float, optional): Mixes dry and wet signals.
        level (float, optional): Output level adjustment.
        threshold (float, optional): Clipping threshold.
        hardness (float, optional): Determines the hardness of the clipping.
        use_wave_shaper (bool, optional): If True, uses wave shaping.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    valid_modes = ["Soft Clipping", "Hard Clipping", "Overdrive", "Fuzz", "Leveller"]

    if mode is not None and mode not in valid_modes:
        raise PyAudacityException(f"mode must be one of {valid_modes}, got {mode}")
    if drive is not None and not isinstance(drive, (float, int)):
        raise PyAudacityException("drive must be float or int, not " + str(type(drive)))
    if tone is not None and not isinstance(tone, (float, int)):
        raise PyAudacityException("tone must be float or int, not " + str(type(tone)))
    if compensate is not None and not isinstance(compensate, bool):
        raise PyAudacityException(
            "compensate must be bool, not " + str(type(compensate))
        )
    if blend is not None and not isinstance(blend, (float, int)):
        raise PyAudacityException("blend must be float or int, not " + str(type(blend)))
    if level is not None and not isinstance(level, (float, int)):
        raise PyAudacityException("level must be float or int, not " + str(type(level)))
    if threshold is not None and not isinstance(threshold, (float, int)):
        raise PyAudacityException(
            "threshold must be float or int, not " + str(type(threshold))
        )
    if hardness is not None and not isinstance(hardness, (float, int)):
        raise PyAudacityException(
            "hardness must be float or int, not " + str(type(hardness))
        )
    if use_wave_shaper is not None and not isinstance(use_wave_shaper, bool):
        raise PyAudacityException(
            "use_wave_shaper must be bool, not " + str(type(use_wave_shaper))
        )

    macro_arguments = []
    if mode is not None:
        macro_arguments.append(f'Mode="{mode}"')
    if drive is not None:
        macro_arguments.append(f'Drive="{drive}"')
    if tone is not None:
        macro_arguments.append(f'Tone="{tone}"')
    if compensate is not None:
        macro_arguments.append(f'Compensate="{int(compensate)}"')
    if blend is not None:
        macro_arguments.append(f'Blend="{blend}"')
    if level is not None:
        macro_arguments.append(f'Level="{level}"')
    if threshold is not None:
        macro_arguments.append(f'Threshold="{threshold}"')
    if hardness is not None:
        macro_arguments.append(f'Hardness="{hardness}"')
    if use_wave_shaper is not None:
        macro_arguments.append(f'UseWaveShaper="{int(use_wave_shaper)}"')

    return do("Distortion: " + " ".join(macro_arguments))


def filter_curve(preset = None, points = None) -> str: # Optional[str], Optional[List[Tuple[float, float]]]
    """Adjusts the volume levels of particular frequencies using a filter curve.

    Parameters:
        preset (str, optional): Name of a predefined preset to use.
        points (list of tuple, optional): List of frequency (Hz) and gain (dB) pairs defining the curve.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    if preset is not None and not isinstance(preset, str):
        raise PyAudacityException("preset must be str, not " + str(type(preset)))
    if points is not None:
        if not isinstance(points, list):
            raise PyAudacityException("points must be a list of tuples")
        for point in points:
            if not (isinstance(point, tuple) and len(point) == 2):
                raise PyAudacityException(
                    "each point must be a tuple of (frequency, gain)"
                )
            freq, gain = point
            if not isinstance(freq, (float, int)):
                raise PyAudacityException("frequency must be float or int")
            if not isinstance(gain, (float, int)):
                raise PyAudacityException("gain must be float or int")

    macro_arguments = []
    if preset is not None:
        macro_arguments.append(f'Preset="{preset}"')
    if points is not None:
        # Convert points to a string format expected by Audacity
        curve_str = (
            'Curve="(' + " ".join(f"{freq} {gain}" for freq, gain in points) + ')"'
        )
        macro_arguments.append(curve_str)

    return do("FilterCurve: " + " ".join(macro_arguments))


def graphic_eq(band_gains = None, preset = None) -> str: # Optional[Dict[float, float]], Optional[str]
    """Adjusts the volume levels of particular frequencies using a graphic equalizer.

    Parameters:
        band_gains (dict of float: float, optional): Dictionary mapping center frequencies to gain values.
        preset (str, optional): Name of a predefined preset to use.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    if band_gains is not None:
        if not isinstance(band_gains, dict):
            raise PyAudacityException("band_gains must be a dict of frequency: gain")
        for freq, gain in band_gains.items():
            if not isinstance(freq, (float, int)):
                raise PyAudacityException("frequency must be float or int")
            if not isinstance(gain, (float, int)):
                raise PyAudacityException("gain must be float or int")
    if preset is not None and not isinstance(preset, str):
        raise PyAudacityException("preset must be str, not " + str(type(preset)))

    macro_arguments = []
    if preset is not None:
        macro_arguments.append(f'Preset="{preset}"')
    if band_gains is not None:
        # Convert band gains to a string format expected by Audacity
        bands_str = " ".join(f"{freq} {gain}" for freq, gain in band_gains.items())
        macro_arguments.append(f'Bands="({bands_str})"')

    return do("GraphicEq: " + " ".join(macro_arguments))


def screenshot(
    save_images_to_folder = Path.home(),
    capture="Window Only",
    background="None",
    to_top = True,
) -> str: # Union[Path, str], str, str, bool
    """Captures a screenshot of Audacity.

    Parameters:
        save_images_to_folder (Path or str, optional): The folder where the screenshot will be saved.
        capture (str, optional): What to capture ('Window Only', 'Window and Dialogs', 'Full Screen').
        background (str, optional): Background color ('None', 'Transparent', 'White').
        to_top (bool, optional): Whether to bring the Audacity window to the top before capturing.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or invalid values.
    """
    valid_captures = ["Window Only", "Window and Dialogs", "Full Screen"]
    valid_backgrounds = ["None", "Transparent", "White"]

    if not isinstance(save_images_to_folder, (Path, str)):
        raise PyAudacityException("save_images_to_folder must be Path or str")
    if capture not in valid_captures:
        raise PyAudacityException(
            f"capture must be one of {valid_captures}, got {capture}"
        )
    if background not in valid_backgrounds:
        raise PyAudacityException(
            f"background must be one of {valid_backgrounds}, got {background}"
        )
    if not isinstance(to_top, bool):
        raise PyAudacityException("to_top must be bool, not " + str(type(to_top)))

    folder = str(save_images_to_folder)
    macro_arguments = [
        f'SaveImagesToFolder="{folder}"',
        f'Capture="{capture}"',
        f'Background="{background}"',
        f'ToTop="{int(to_top)}"',
    ]

    return do("Screenshot: " + " ".join(macro_arguments))


def benchmark() -> str:
    """Runs the benchmark tool to measure the performance of Audacity.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("Benchmark")


def nyquist_prompt(command="", version = 3) -> str: # str, int
    """Executes a Nyquist command.

    Parameters:
        command (str, optional): The Nyquist code to execute.
        version (int, optional): The Nyquist version to use (2 or 3).

    Returns:
        str: The result of the Nyquist command execution.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    if not isinstance(command, str):
        raise PyAudacityException("command must be str, not " + str(type(command)))
    if version not in [2, 3]:
        raise PyAudacityException("version must be 2 or 3, got " + str(version))

    command_str = f'NyquistPrompt: Command="{command}" Version="{version}"'
    return do(command_str)


def nyquist_plugin_installer(files = None, overwrite="Disallow") -> str: # Optional[Union[str, List[str]]], str
    """Installs Nyquist plugins.

    Parameters:
        files (str or list of str, optional): The file path(s) of the plugins to install.
        overwrite (str, optional): Overwrite mode ('Disallow', 'Allow', 'Rename').

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    valid_overwrite = ["Disallow", "Allow", "Rename"]

    if files is not None:
        if isinstance(files, str):
            files_str = files
        elif isinstance(files, list) and all(isinstance(f, str) for f in files):
            files_str = ";".join(files)
        else:
            raise PyAudacityException("files must be a str or list of str")
    else:
        files_str = ""

    if overwrite not in valid_overwrite:
        raise PyAudacityException(
            f"overwrite must be one of {valid_overwrite}, got {overwrite}"
        )

    command_str = f'NyquistPluginInstaller: Files="{files_str}" Overwrite="{overwrite}"'
    return do(command_str)


def sample_data_import(import_filename, invalid_data_handling="Throw Error") -> str: # Union[Path, str], str
    """Imports numeric sample data from a plain ASCII text file.

    Parameters:
        import_filename (str or Path): The path to the text file containing sample data.
        invalid_data_handling (str, optional): How to handle invalid data ('Throw Error', 'Replace with Zero', 'Skip').

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If arguments are of incorrect types or values.
    """
    valid_handling = ["Throw Error", "Replace with Zero", "Skip"]

    if not isinstance(import_filename, (str, Path)):
        raise PyAudacityException("import_filename must be str or Path")
    if invalid_data_handling not in valid_handling:
        raise PyAudacityException(
            f"invalid_data_handling must be one of {valid_handling}, got {invalid_data_handling}"
        )

    filename = str(import_filename)
    command_str = f'SampleDataImport2: Filename="{filename}" InvalidDataHandling="{invalid_data_handling}"'
    return do(command_str)


def help() -> str:
    """Provides help information for scripting commands.

    Returns:
        str: The help information.
    """
    return do("Help")


def drag(id = None, x = None, y = None, to_x = None, to_y = None, window = None, to_window = None) -> str: # Optional[str], Optional[int], Optional[int], Optional[int], Optional[int], Optional[str], Optional[str]
    """Simulates mouse movements and drags within Audacity.

    Parameters:
        id (str, optional): The ID of the GUI element to interact with.
        x (int, optional): The X-coordinate to move the mouse to.
        y (int, optional): The Y-coordinate to move the mouse to.
        to_x (int, optional): The X-coordinate to drag the mouse to.
        to_y (int, optional): The Y-coordinate to drag the mouse to.
        window (str, optional): The window name to interact with.
        to_window (str, optional): The window name to drag the mouse to.

    Returns:
        str: The response from Audacity after executing the command.

    Raises:
        PyAudacityException: If parameters are invalid.
    """
    if id is not None and not isinstance(id, str):
        raise PyAudacityException("id must be str")
    if x is not None and not isinstance(x, int):
        raise PyAudacityException("x must be int")
    if y is not None and not isinstance(y, int):
        raise PyAudacityException("y must be int")
    if to_x is not None and not isinstance(to_x, int):
        raise PyAudacityException("to_x must be int")
    if to_y is not None and not isinstance(to_y, int):
        raise PyAudacityException("to_y must be int")
    if window is not None and not isinstance(window, str):
        raise PyAudacityException("window must be str")
    if to_window is not None and not isinstance(to_window, str):
        raise PyAudacityException("to_window must be str")

    macro_arguments = []
    if id is not None:
        macro_arguments.append(f'Id="{id}"')
    if x is not None:
        macro_arguments.append(f'X="{x}"')
    if y is not None:
        macro_arguments.append(f'Y="{y}"')
    if to_x is not None:
        macro_arguments.append(f'ToX="{to_x}"')
    if to_y is not None:
        macro_arguments.append(f'ToY="{to_y}"')
    if window is not None:
        macro_arguments.append(f'Window="{window}"')
    if to_window is not None:
        macro_arguments.append(f'ToWindow="{to_window}"')

    return do("Drag: " + " ".join(macro_arguments))


def compare_audio() -> str:
    """Compares the selected range on two tracks and reports on the differences and similarities.

    Returns:
        str: The comparison report.

    Raises:
        PyAudacityException: If the selection is invalid.
    """
    return do("CompareAudio")


def quick_help() -> str:
    """Provides a brief version of help with essential information.

    Returns:
        str: The quick help information.
    """
    return do("QuickHelp")


def manual() -> str:
    """Opens the Audacity manual in the default browser.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("Manual")


def updates() -> str:
    """Checks online to see if this is the latest version of Audacity.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("Updates")


def about() -> str:
    """Displays information about Audacity, including version and license.

    Returns:
        str: The response from Audacity after executing the command.
    """
    return do("About")


def device_info() -> str:
    """Shows technical information about your detected audio device(s).

    Returns:
        str: The device information.
    """
    return do("DeviceInfo")


def midi_device_info() -> str:
    """Shows technical information about your detected MIDI device(s).

    Returns:
        str: The MIDI device information.
    """
    return do("MidiDeviceInfo")


def log() -> str:
    """TODO

    Audacity Documentation: Launches the "Audacity Log" window, the log is largely a debugging aid, having timestamps for each entry.
    """
    return do("Log")


def crash_report() -> str:
    """TODO

    Audacity Documentation: Selecting this will generate a Debug report which could be useful in aiding the developers to identify bugs in Audacity or in third-party plugins.
    """
    return do("CrashReport")


def check_deps() -> str:
    """TODO

    Audacity Documentation: Lists any WAV or AIFF audio files that your project depends on, and allows you to copy these files into the project.
    """
    return do("CheckDeps")


def prev_window() -> str:
    """TODO

    Audacity Documentation: Navigates to the previous window."""
    return do("PrevWindow")


def next_window() -> str:
    """TODO

    Audacity Documentation: Navigates to the next window."""
    return do("NextWindow")
