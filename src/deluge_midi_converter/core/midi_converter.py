# MidiConverter.py
import os
import pretty_midi
from deluge_midi_converter.core import xml_injector
import xml.etree.ElementTree as ET
import math
import logging
from typing import List, Dict, Union
import argparse


def hex_lz32(v: int) -> str:
    """
    Converts an integer to an 8-character uppercase hexadecimal string with leading zeros.
    """
    return f"{v & 0xFFFFFFFF:08X}"


def make_range_mapper(o_min: float, o_max: float, n_min: float, n_max: float):
    """
    Returns a function that maps a value from the original range to the new range,
    handling reversed ranges.
    """
    if o_min == o_max:
        print("Warning: Zero input range")
        return lambda x: None

    if n_min == n_max:
        print("Warning: Zero output range")
        return lambda x: None

    reverse_input = o_min > o_max
    reverse_output = n_min > n_max

    old_min, old_max = (o_max, o_min) if reverse_input else (o_min, o_max)
    new_min, new_max = (n_max, n_min) if reverse_output else (n_min, n_max)

    def mapper(x):
        return ((x - old_min) * (new_max - new_min) / (old_max - old_min)) + new_min

    if reverse_input:

        def mapper_reverse(x):
            return ((old_max - x) * (new_max - new_min) / (old_max - old_min)) + new_min

        return mapper_reverse

    if reverse_output:

        def mapper_reverse_output(x):
            portion = (x - old_min) * (new_max - new_min) / (old_max - old_min)
            return new_max - portion

        return mapper_reverse_output

    return mapper


class ConversionContext:
    """
    Handles time and PPQ (Pulses Per Quarter note) conversions.
    """

    def __init__(
        self,
        source_ppq: int,
        dest_ppq: int = 48,
        tick_offset: int = 0,
        start_time: float = 0.0,
        end_time: float = math.inf,
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.tick_offset = tick_offset
        self.source_ppq = source_ppq
        self.dest_ppq = dest_ppq
        self.scale_value_by = 1

    def convert_time(self, t: int) -> int:
        """
        Converts source ticks to destination ticks.
        Rounds early to prevent floating point precision issues.
        """
        return round((t * self.dest_ppq) / self.source_ppq)

    def convert_time_ro(self, t: int) -> int:
        """
        Converts source ticks to destination ticks with tick offset.
        """
        return self.convert_time(t - self.tick_offset)

    def convert_time_dtos(self, t: int) -> int:
        """
        Converts destination ticks back to source ticks.
        """
        return round((t * self.source_ppq) / self.dest_ppq)


class MidiConverter:
    """
    Converts MIDI files to Deluge Synthstrom song XML format.
    """

    def __init__(self, midi_path: str):
        """
        Initializes the MidiConverter with the path to the MIDI file.
        """
        self.midi_path = midi_path
        try:
            self.midi = pretty_midi.PrettyMIDI(midi_path)
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Loaded MIDI file: {midi_path}")
        except Exception as e:
            self.logger.error(f"Failed to load MIDI file '{midi_path}'. Error: {e}")
            raise

    def convert_norm_to_hex(self, v: float) -> str:
        """
        Converts a normalized value (0.0 to 1.0) to a 32-bit hexadecimal string.
        """
        # Ensure v is within bounds
        v = max(0.0, min(1.0, v))
        value = round(v * 0x7FFFFFFF) - 0x40000000
        return hex_lz32(value)

    def convert_midi_to_clips(
        self,
    ) -> List[Dict[str, Union[List[Dict[str, str]], int]]]:
        """
        Converts the MIDI file into a list of clip data dictionaries.
        Each dictionary contains 'note_rows' and 'length'.
        """
        clip_data = []
        for track_num, instrument in enumerate(self.midi.instruments, start=1):
            if instrument.is_drum:
                self.logger.info(f"Skipping drum track {track_num}.")
                continue

            self.logger.info(f"Processing track {track_num}: {instrument.program}")

            notes = instrument.notes
            if not notes:
                self.logger.warning(f"No notes found in track {track_num}. Skipping.")
                continue

            # Sort notes by start time
            notes_sorted = sorted(notes, key=lambda n: n.start)

            # Calculate ClipMax (track length in destination ticks)
            max_tick = max(self.midi.time_to_tick(note.end) for note in notes_sorted)
            context = ConversionContext(
                source_ppq=self.midi.resolution,
                dest_ppq=48,
                tick_offset=0,
                start_time=0.0,
                end_time=self.midi.get_end_time(),
            )

            clip_max = context.convert_time(math.ceil(max_tick))

            # Organize notes by pitch
            lanes: Dict[int, List[pretty_midi.Note]] = {}
            for note in notes_sorted:
                pitch = note.pitch
                lanes.setdefault(pitch, []).append(note)

            note_rows = []
            for pitch, pitch_notes in lanes.items():
                laneh = "0x"
                last_start = -1
                last_end = -1

                # Sort notes by start time within the lane
                pitch_notes_sorted = sorted(pitch_notes, key=lambda n: n.start)

                for note in pitch_notes_sorted:
                    t_start_tick = self.midi.time_to_tick(note.start)
                    t_dur_tick = self.midi.time_to_tick(note.end) - t_start_tick
                    t_end_tick = t_start_tick + t_dur_tick

                    if t_start_tick <= last_start:
                        self.logger.warning(
                            f"*** Out of order MIDI: {t_start_tick} <= {last_start} in track {track_num}"
                        )
                    if t_start_tick < last_end:
                        self.logger.warning(
                            f"*** Overlapping note: {t_start_tick} <= {last_end} in track {track_num}"
                        )

                    last_start = t_start_tick
                    last_end = t_end_tick

                    # Convert timing using context
                    t_dstart = context.convert_time(t_start_tick)
                    t_ddur = context.convert_time(t_dur_tick)
                    t_dnote_end = t_dstart + t_ddur

                    # Update clip_max if necessary
                    if t_dnote_end > clip_max:
                        clip_max = t_dnote_end

                    # Handle velocity conversion
                    t_dvel = min(
                        round(note.velocity), 127
                    )  # Ensure velocity is capped at 127

                    # Fixed parameters
                    lift_val = "40"  # Standard lift value
                    h_cc = "14"  # Standard CC value

                    # Construct hex string components
                    h_start = hex_lz32(t_dstart)
                    h_dur = hex_lz32(t_ddur)
                    h_vel = f"{t_dvel:02X}"
                    h = h_start + h_dur + h_vel + lift_val + h_cc

                    laneh += h.upper()

                note_row = {"y": str(pitch), "noteDataWithLift": laneh}
                note_rows.append(note_row)

            # Sort note_rows by 'y' in ascending order
            note_rows_sorted = sorted(note_rows, key=lambda x: int(x["y"]))

            # Log the sorted 'y' values for verification
            sorted_y_values = [int(nr["y"]) for nr in note_rows_sorted]
            self.logger.info(
                f"Sorted y values for track {track_num}: {sorted_y_values}"
            )

            clip_data.append({"note_rows": note_rows_sorted, "length": clip_max})
            self.logger.info(f"Processed track {track_num}: Length={clip_max} ticks")

        return clip_data

    def convert(self, output_xml_path: str):
        """
        Converts the MIDI file and injects the data into the XML.
        """
        try:
            self.logger.info("Starting MIDI to Deluge XML conversion...")
            clip_data = self.convert_midi_to_clips()

            if not clip_data:
                self.logger.warning("No clip data to inject. Conversion aborted.")
                return

            injector = xml_injector.XMLInjector()
            success = injector.inject_multiple_clips(clip_data)

            if success:
                self.logger.info(f"Successfully created Deluge XML: {output_xml_path}")
            else:
                self.logger.error("Failed to inject clip data into XML.")

        except Exception as e:
            self.logger.error(f"Conversion failed. Error: {e}")
            raise


def setup_logging():
    """
    Configures the logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main():
    """
    Main function to handle command-line arguments and initiate conversion.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Convert MIDI files to Deluge Synthstrom song XML."
    )
    parser.add_argument(
        "--midi_path",
        type=str,
        required=True,
        help="Path to the input MIDI file.",
    )
    parser.add_argument(
        "--output_xml",
        type=str,
        required=True,
        help="Path to the output Deluge XML file.",
    )

    args = parser.parse_args()

    midi_path = args.midi_path
    output_xml = args.output_xml

    if not os.path.exists(midi_path):
        logger.error(f"MIDI file '{midi_path}' does not exist.")
        return

    converter = MidiConverter(midi_path)
    converter.convert(output_xml)


if __name__ == "__main__":
    main()
