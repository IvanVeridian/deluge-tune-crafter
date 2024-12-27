import os
import logging
from tqdm import tqdm
from deluge_midi_converter.core.basic_pitch_processor import batch_process
from deluge_midi_converter.core.midi_converter import MidiConverter
from deluge_midi_converter.core.xml_injector import XMLInjector
from pathlib import Path
import glob
import shutil
import re
import sys


def sanitize_filename(filename):
    """
    Removes or replaces characters that are invalid in filenames.
    """
    return re.sub(r'[<>:"/\\|?*]', "_", filename)


def setup_logging():
    """
    Configures the logging settings.
    """
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/app.log", mode="a"),
        ],
    )


def run_full_process(
    input_folder,
    midi_output_folder,
    xml_output_folder,
    base_xml_path,
    sonify_midi,
    save_model_outputs,
    save_notes,
):
    """
    Runs the full process of converting audio to MIDI and then to XML.
    """
    logger = logging.getLogger(__name__)
    # Step 1: Process audio files to MIDI
    logger.info("Starting audio to MIDI conversion using BasicPitchProcessor...")
    batch_process(
        input_folder=input_folder,
        output_folder=midi_output_folder,
        save_midi=True,
        sonify_midi=sonify_midi,
        save_model_outputs=save_model_outputs,
        save_notes=save_notes,
    )
    logger.info("Audio to MIDI conversion completed.")

    # Step 2: Collect all generated MIDI files
    midi_pattern = os.path.join(midi_output_folder, "*_basic_pitch.mid")
    midi_files = glob.glob(midi_pattern)
    if not midi_files:
        logger.error(f"No MIDI files found in '{midi_output_folder}'. Aborting.")
        return

    logger.info(f"Found {len(midi_files)} MIDI file(s) to convert.")

    # Step 3: Convert MIDI files to clip data
    all_clip_data = []
    original_filename = None
    for midi_file in tqdm(midi_files, desc="Converting MIDI to Clip Data"):
        try:
            converter = MidiConverter(midi_file)
            clip_data = converter.convert_midi_to_clips()
            all_clip_data.extend(clip_data)
            logger.info(f"Converted '{midi_file}' to clip data.")
            
            # Store the original filename from the first MIDI file
            if original_filename is None:
                # Get the original audio filename by removing '_basic_pitch.mid'
                original_filename = Path(midi_file).stem.replace('_basic_pitch', '')
                
        except Exception as e:
            logger.error(f"Failed to convert '{midi_file}'. Error: {e}")

    logger.info(f"Total clip data collected: {len(all_clip_data)} clips.")

    if not all_clip_data:
        logger.error("No clip data generated from MIDI files. Aborting XML injection.")
        return

    # Step 4: Inject clip data into XML
    injector = XMLInjector(base_xml_path=base_xml_path)
    success = injector.inject_multiple_clips(all_clip_data)

    if success:
        logger.info("Clip data successfully injected into XML.")
        # Move the generated 'output.xml' to the desired final output path
        generated_xml_path = Path("data/deluge_songs/output.xml")
        
        # Use the original filename for the output XML
        if original_filename:
            final_output_path = Path(xml_output_folder) / f"{original_filename}.xml"
        else:
            final_output_path = Path(xml_output_folder) / "final_deluge_song.xml"

        if generated_xml_path.exists():
            try:
                shutil.move(str(generated_xml_path), str(final_output_path))
                logger.info(f"Final Deluge XML saved to: {final_output_path}")
            except Exception as e:
                logger.error(
                    f"Failed to move '{generated_xml_path}' to '{final_output_path}'. Error: {e}"
                )
        else:
            logger.error(f"Expected output XML '{generated_xml_path}' not found.")
    else:
        logger.error("Failed to inject clip data into XML.")


def run_using_existing_midi(midi_output_folder, xml_output_folder, base_xml_path):
    """
    Uses existing MIDI files from the folder and converts them to XML.
    """
    logger = logging.getLogger(__name__)

    # Use existing MIDI files from the folder
    midi_folder = Path(midi_output_folder)
    midi_pattern = midi_folder.glob("*.mid")
    midi_files = [str(file) for file in midi_pattern if file.is_file()]
    if not midi_files:
        logger.error(f"No MIDI files found in '{midi_output_folder}'. Aborting.")
        return
    logger.info(f"Found {len(midi_files)} existing MIDI file(s) to convert.")

    # Determine processing mode based on the number of MIDI files
    if len(midi_files) > 1:
        # Prompt the user for processing mode
        while True:
            print("\nMultiple MIDI files detected.")
            print("Choose how to process the MIDI files:")
            print("1. Insert all MIDI files into a single XML.")
            print("2. Create separate XMLs for each MIDI file.")
            choice = input("Enter 1 or 2: ").strip()
            if choice == "1":
                process_mode = "single"
                break
            elif choice == "2":
                process_mode = "multiple"
                break
            else:
                print("Invalid choice. Please enter 1 or 2.")
    else:
        # Only one MIDI file, default to single XML
        process_mode = "single"

    all_clip_data = []
    if process_mode == "single":
        # Convert all MIDI files and aggregate clip data
        first_midi_filename = None
        for midi_file in tqdm(midi_files, desc="Converting MIDI to Clip Data"):
            try:
                converter = MidiConverter(midi_file)
                clip_data = converter.convert_midi_to_clips()
                all_clip_data.extend(clip_data)
                logger.info(f"Converted '{midi_file}' to clip data.")
                
                # Store the first MIDI filename for the output
                if first_midi_filename is None:
                    first_midi_filename = Path(midi_file).stem
                
            except Exception as e:
                logger.error(f"Failed to convert '{midi_file}'. Error: {e}")

        logger.info(f"Total clip data collected: {len(all_clip_data)} clips.")

        if not all_clip_data:
            logger.error(
                "No clip data generated from MIDI files. Aborting XML injection."
            )
            return

        # Step 4: Inject clip data into XML
        injector = XMLInjector(base_xml_path=base_xml_path)
        success = injector.inject_multiple_clips(all_clip_data)

        if success:
            logger.info("Clip data successfully injected into XML.")
            # Move the generated 'output.xml' to the desired final output path
            generated_xml_path = Path("data/deluge_songs/output.xml")
            
            # Use the first MIDI filename for the combined output
            if first_midi_filename:
                final_output_path = Path(xml_output_folder) / f"{first_midi_filename}_combined.xml"
            else:
                final_output_path = Path(xml_output_folder) / "combined_deluge_song.xml"

            if generated_xml_path.exists():
                try:
                    shutil.move(str(generated_xml_path), str(final_output_path))
                    logger.info(f"Combined Deluge XML saved to: {final_output_path}")
                except Exception as e:
                    logger.error(
                        f"Failed to move '{generated_xml_path}' to '{final_output_path}'. Error: {e}"
                    )
            else:
                logger.error(f"Expected output XML '{generated_xml_path}' not found.")
        else:
            logger.error("Failed to inject clip data into XML.")

    elif process_mode == "multiple":
        # Process each MIDI file separately
        for midi_file in midi_files:
            all_clip_data = []
            try:
                converter = MidiConverter(midi_file)
                clip_data = converter.convert_midi_to_clips()
                all_clip_data.extend(clip_data)
                logger.info(f"Converted '{midi_file}' to clip data.")
            except Exception as e:
                logger.error(f"Failed to convert '{midi_file}'. Error: {e}")
                continue  # Skip to the next MIDI file

            logger.info(
                f"Total clip data collected for '{midi_file}': {len(all_clip_data)} clips."
            )

            if not all_clip_data:
                logger.error(
                    f"No clip data generated from '{midi_file}'. Skipping XML injection."
                )
                continue

            # Step 4: Inject clip data into XML
            injector = XMLInjector(base_xml_path=base_xml_path)
            success = injector.inject_multiple_clips(all_clip_data)

            if success:
                logger.info(
                    f"Clip data successfully injected into XML for '{midi_file}'."
                )
                # Move the generated 'output.xml' to the desired final output path
                midi_filename = sanitize_filename(Path(midi_file).stem)
                final_output_path = Path(xml_output_folder) / f"{midi_filename}.xml"

                generated_xml_path = Path("data/deluge_songs/output.xml")

                if generated_xml_path.exists():
                    try:
                        shutil.move(str(generated_xml_path), str(final_output_path))
                        logger.info(
                            f"Deluge XML for '{midi_filename}' saved to: {final_output_path}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to save '{midi_filename}.xml'. Error: {e}"
                        )
                else:
                    logger.error(
                        f"Expected output XML '{generated_xml_path}' not found for '{midi_filename}'."
                    )
            else:
                logger.error(f"Failed to inject clip data into XML for '{midi_file}'.")


def main_menu():
    """
    Displays the interactive menu and gets the user's choice.
    """
    print("\n=== Audio to MIDI/XML Converter ===")
    print("Please select an option:")
    print("1. Run the full process (convert audio files from 'audio_input' folder to MIDI and then to XML)")
    print("2. Convert existing MIDI files from 'input_midi' folder to XML")
    print("3. Exit")
    choice = input("Enter the number of your choice (1, 2, or 3): ").strip()
    return choice


def main():
    """
    Main function to orchestrate the conversion process based on user input.
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    # Define default paths using the new directory structure
    default_input_folder = "data/audio_input"
    default_input_midi_folder = "data/input_midi"  # New folder for input MIDI files
    default_midi_output_folder = "data/converted_midi"
    default_xml_output_folder = "data/deluge_songs"
    default_base_xml_path = "src/deluge_midi_converter/resources/base.XML"

    while True:
        choice = main_menu()

        if choice == "1":
            print("\n--- Full Process: Audio to MIDI to XML ---")

            # Use default paths without prompting the user
            input_folder = default_input_folder
            midi_output_folder = default_midi_output_folder
            xml_output_folder = default_xml_output_folder
            base_xml_path = default_base_xml_path

            # Configuration flags with default values
            sonify_midi = False
            save_model_outputs = False
            save_notes = False

            # Optional: If you want to allow users to enable these flags,
            # you can add simple yes/no prompts without asking for paths.

            # Example:
            sonify_midi_input = (
                input("Enable MIDI sonification? (y/n) [n]: ").strip().lower()
            )
            if sonify_midi_input == "y":
                sonify_midi = True

            save_model_outputs_input = (
                input("Save model outputs during processing? (y/n) [n]: ")
                .strip()
                .lower()
            )
            if save_model_outputs_input == "y":
                save_model_outputs = True

            save_notes_input = (
                input("Save notes information? (y/n) [n]: ").strip().lower()
            )
            if save_notes_input == "y":
                save_notes = True

            # Ensure the MIDI and XML output directories exist
            Path(midi_output_folder).mkdir(parents=True, exist_ok=True)
            Path(xml_output_folder).mkdir(parents=True, exist_ok=True)

            # Run the full process
            run_full_process(
                input_folder=input_folder,
                midi_output_folder=midi_output_folder,
                xml_output_folder=xml_output_folder,
                base_xml_path=base_xml_path,
                sonify_midi=sonify_midi,
                save_model_outputs=save_model_outputs,
                save_notes=save_notes,
            )

        elif choice == "2":
            print("\n--- Existing MIDI to XML Conversion ---")
            print(f"Please ensure your MIDI files are placed in the '{default_input_midi_folder}' folder.")
            print("The program will convert all MIDI files found in this folder.\n")

            # Use default paths without prompting the user
            midi_input_folder = default_input_midi_folder  # Use the new input MIDI folder
            xml_output_folder = default_xml_output_folder
            base_xml_path = default_base_xml_path

            # Ensure the XML output directory exists
            Path(xml_output_folder).mkdir(parents=True, exist_ok=True)

            # Run using existing MIDI files
            run_using_existing_midi(
                midi_output_folder=midi_input_folder,  # Use the input MIDI folder here
                xml_output_folder=xml_output_folder,
                base_xml_path=base_xml_path,
            )

        elif choice == "3":
            print("Exiting the program. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main()
