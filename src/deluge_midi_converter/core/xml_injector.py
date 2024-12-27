import xml.etree.ElementTree as ET
from typing import List, Dict, Union, Set
import logging
from pathlib import Path
import copy
import random


class XMLInjector:
    """
    Handles injection of note data and length updates into Deluge XML file,
    supporting multiple instrument clips with unique presets and colors.
    """

    PRESET_NAMES = [
        "000 Rich Saw Bass",
        "001 Sync Bass",
        "002 Basic Square Bass",
        "003 Synthwave Bass",
        "005 Sweet Mono Bass",
        "006 Vaporwave Bass",
        "007 Detuned Saw Bass",
        "009 Hoover Bass",
        "019 Fizzy Strings",
        "026 Pw Organ",
        "030 Distant Porta",
        "040 Spacer Leader",
        "073 Piano",
        "074 Electric Piano",
        "076 Organ",
        "078 House",
    ]

    def __init__(self, base_xml_path: str = "data/deluge_songs/base.XML"):
        """
        Initialize the XML injector with path to base XML file.
        """
        self.base_xml_path = Path(base_xml_path)
        self.logger = logging.getLogger(__name__)
        self.used_presets: Set[str] = set()
        self.used_colors: Set[int] = set()

    def get_unique_preset(self) -> str:
        """
        Get a unique preset name that hasn't been used yet.
        """
        available_presets = set(self.PRESET_NAMES) - self.used_presets
        if not available_presets:
            raise ValueError("No more unique presets available")

        preset = random.choice(list(available_presets))
        self.used_presets.add(preset)
        return preset

    def get_unique_color(self) -> int:
        """
        Get a unique color offset between -63 and 63.
        """
        available_colors = set(range(-63, 64)) - self.used_colors
        if not available_colors:
            raise ValueError("No more unique colors available")

        color = random.choice(list(available_colors))
        self.used_colors.add(color)
        return color

    def load_xml(self) -> ET.ElementTree:
        """
        Load the base XML file into an ElementTree.
        """
        try:
            tree = ET.parse(self.base_xml_path)
            return tree
        except Exception as e:
            self.logger.error(f"Failed to load base XML: {e}")
            raise

    def inject_multiple_clips(
        self, clip_data: List[Dict[str, Union[List[Dict], int]]]
    ) -> bool:
        """
        Inject multiple sets of note rows, creating new instrument clips as needed.
        Each clip gets a unique instrument preset and color.
        """
        try:
            if len(clip_data) > len(self.PRESET_NAMES):
                raise ValueError(
                    f"Too many clips ({len(clip_data)}). Maximum allowed: {len(self.PRESET_NAMES)}"
                )

            tree = self.load_xml()
            root = tree.getroot()

            # Reset used presets and colors
            self.used_presets.clear()
            self.used_colors.clear()

            # Find the sessionClips element
            session_clips = root.find(".//sessionClips")
            if session_clips is None:
                raise ValueError("Could not find sessionClips element")

            # Get the template instrument clip
            template_clip = session_clips.find("instrumentClip")
            if template_clip is None:
                raise ValueError("Could not find template instrumentClip")

            # Clear existing instrument clips
            session_clips.clear()

            # Process each set of clip data
            for data in clip_data:
                # Create a deep copy of the template clip
                new_clip = copy.deepcopy(template_clip)

                # Always set section to 0
                new_clip.set("section", "0")

                # Set unique preset name
                new_clip.set("instrumentPresetName", self.get_unique_preset())

                # Set unique color offset
                new_clip.set("colourOffset", str(self.get_unique_color()))

                # Update length
                new_clip.set("length", str(data["length"]))

                # Find and clear noteRows
                note_rows_element = new_clip.find(".//noteRows")
                if note_rows_element is None:
                    raise ValueError("Could not find noteRows")
                note_rows_element.clear()

                # Add new note rows
                for note_row in data["note_rows"]:
                    row_element = ET.SubElement(note_rows_element, "noteRow")
                    row_element.set("y", note_row["y"])
                    row_element.set("noteDataWithLift", note_row["noteDataWithLift"])

                # Add the new clip to sessionClips
                session_clips.append(new_clip)

            # Save the modified XML
            output_path = Path("data/deluge_songs/output.xml")
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            self.logger.info(
                f"Successfully wrote modified XML with {len(clip_data)} clips to {output_path}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to inject multiple clips: {e}")
            return False

    def validate_clip_data(
        self, clip_data: List[Dict[str, Union[List[Dict], int]]]
    ) -> bool:
        """
        Validate clip data structure and contents.
        """
        try:
            if len(clip_data) > len(self.PRESET_NAMES):
                return False

            for clip in clip_data:
                if not isinstance(clip, dict):
                    return False
                if "note_rows" not in clip or "length" not in clip:
                    return False
                if not isinstance(clip["length"], int):
                    return False
                if not isinstance(clip["note_rows"], list):
                    return False
                for note_row in clip["note_rows"]:
                    if not self.validate_note_row(note_row):
                        return False
            return True
        except Exception:
            return False

    def validate_note_row(self, note_row: Dict[str, str]) -> bool:
        """
        Validate a note row dictionary has required fields.
        """
        required_keys = {"y", "noteDataWithLift"}
        return all(key in note_row for key in required_keys)


def main():
    # Example usage
    injector = XMLInjector()

    # Example data for multiple clips
    clip_data = [
        {
            "note_rows": [{"y": "72", "noteDataWithLift": "0x0000000000000018404014"}],
            "length": 384,
        },
        {
            "note_rows": [{"y": "74", "noteDataWithLift": "0x0000000000000018404015"}],
            "length": 768,
        },
    ]

    # Inject the clips
    success = injector.inject_multiple_clips(clip_data)
    if success:
        print("Successfully injected multiple clips")
        print("Used presets:", injector.used_presets)
        print("Used colors:", sorted(list(injector.used_colors)))
    else:
        print("Failed to inject clips")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
