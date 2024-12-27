import os
import argparse
import logging
from tqdm import tqdm
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH


def setup_logging():
    """
    Configures the logging settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def process_audio_file(
    input_audio_path,
    output_directory,
    save_midi=True,
    sonify_midi=False,
    save_model_outputs=False,
    save_notes=False,
):
    """
    Converts a single audio file to MIDI using Basic Pitch.

    Parameters:
    - input_audio_path (str): Path to the input audio file.
    - output_directory (str): Directory to save the MIDI file and other outputs.
    - save_midi (bool): Whether to save the MIDI file.
    - sonify_midi (bool): Whether to save a WAV rendering of the MIDI.
    - save_model_outputs (bool): Whether to save raw model outputs.
    - save_notes (bool): Whether to save predicted note events as CSV.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_directory, exist_ok=True)

        # Get the base filename without extension
        base_name = os.path.splitext(os.path.basename(input_audio_path))[0]
        
        # Remove existing output files if they exist
        midi_path = os.path.join(output_directory, f"{base_name}_basic_pitch.mid")
        if os.path.exists(midi_path):
            os.remove(midi_path)
            logging.info(f"Removed existing MIDI file: {midi_path}")

        # Prepare the arguments for predict_and_save
        input_files = [input_audio_path]

        # Call predict_and_save with all arguments as positional arguments in the correct order
        predict_and_save(
            input_files,                    # audio paths
            output_directory,               # output directory
            save_midi,                      # save midi
            sonify_midi,                    # sonify midi
            save_model_outputs,             # save model outputs
            save_notes,                     # save notes
            ICASSP_2022_MODEL_PATH,         # model path
            0.5,                            # onset threshold
            0.3,                            # frame threshold
            58,                             # minimum note length
            None,                           # minimum frequency
            None,                           # maximum frequency
            False,                          # multiple pitch bends
            True,                           # melodia trick
            None                            # debug file
        )
        logging.info(f"Successfully processed {input_audio_path}")
    except Exception as e:
        logging.error(f"Failed to process {input_audio_path}. Error: {e}")
        raise


def batch_process(
    input_folder,
    output_folder,
    save_midi=True,
    sonify_midi=False,
    save_model_outputs=False,
    save_notes=False,
):
    """
    Processes all supported audio files in the input folder and converts them to MIDI.

    Parameters:
    - input_folder (str): Directory containing input audio files.
    - output_folder (str): Directory to save MIDI files.
    - save_midi (bool): Whether to save MIDI files.
    - sonify_midi (bool): Whether to save WAV renderings of MIDI.
    - save_model_outputs (bool): Whether to save raw model outputs.
    - save_notes (bool): Whether to save predicted note events as CSV.
    """
    # Supported audio file extensions
    supported_extensions = (".mp3", ".wav", ".flac", ".ogg", ".m4a")

    # List all files in the input directory
    try:
        files = os.listdir(input_folder)
    except FileNotFoundError:
        logging.error(f"Input folder '{input_folder}' does not exist.")
        return

    # Filter audio files
    audio_files = [
        file for file in files if file.lower().endswith(supported_extensions)
    ]

    if not audio_files:
        logging.warning(f"No supported audio files found in '{input_folder}'.")
        return

    logging.info(
        f"Found {len(audio_files)} audio file(s) in '{input_folder}'. Starting conversion..."
    )

    # Process each file with a progress bar
    for audio_file in tqdm(audio_files, desc="Processing audio files"):
        input_audio_path = os.path.join(input_folder, audio_file)
        process_audio_file(
            input_audio_path=input_audio_path,
            output_directory=output_folder,
            save_midi=save_midi,
            sonify_midi=sonify_midi,
            save_model_outputs=save_model_outputs,
            save_notes=save_notes,
        )

    logging.info("🎉 All files have been processed.")


if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Batch convert audio files in 'input' folder to MIDI files in 'output' folder using Basic Pitch."
    )
    parser.add_argument(
        "--input_folder",
        type=str,
        default="input",
        help="Path to the input folder containing audio files.",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default="output",
        help="Path to the output folder where MIDI files will be saved.",
    )
    parser.add_argument(
        "--sonify_midi",
        action="store_true",
        help="Flag to save WAV renderings of MIDI files.",
    )
    parser.add_argument(
        "--save_model_outputs",
        action="store_true",
        help="Flag to save raw model outputs as NPZ files.",
    )
    parser.add_argument(
        "--save_notes",
        action="store_true",
        help="Flag to save predicted note events as CSV files.",
    )

    args = parser.parse_args()

    # By default, save_midi is True
    save_midi = True

    batch_process(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        save_midi=save_midi,
        sonify_midi=args.sonify_midi,
        save_model_outputs=args.save_model_outputs,
        save_notes=args.save_notes,
    )
