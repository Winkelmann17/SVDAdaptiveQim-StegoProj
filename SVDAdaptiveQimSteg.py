"""
Author: Winkelmann17, Team 22
Team Members: Winkelmann17, Awesome Partner
Purpose: Implementation of the the JPEG steganography algorithm 
presented by Jing Liu, Xiaofeng Song, Guopeng Li, and Kun Han from
their work "Robust JPEG Image Steganography Using Wavelet Domain SVD
and Adaptive QIM."

NOTE: THIS CODE IS AN IMPLEMENTATION OF PRIOR WORK AND RESEARCH. THIS
CODE IS NOT ORIGINAL IN ITS IDEAS OR IMPLEMENTATION. 

Last Updated: July 27 2026
Recent Changes:
- Reformatted commandline to be easier to understand and read
- Check that provided JPG isn't empty
"""
# Imports
import argparse
import os
from PIL import Image
import sys
import time

from embed import embed
from extract import extract

# Constants
DEFAULT_BLOCKSIZE = 4
MIN_BLOCKSIZE = 2
MAX_BLOCKSIZE = 64
DEFAULT_T_MIN = 20
DEFAULT_T_MAX = 70
T_MIN_MIN = 5
T_MAX_MIN = 10
DEFAULT_WAVELET = "haar"
APPROVED_WAVELETS = ["haar", "db2", "db4", "sym4", "bior1.1", "bior4.4"]

DESC = "Implementation of the the JPEG steganography algorithm " \
"presented by Jing Liu, Xiaofeng Song, Guopeng Li, and Kun Han from" \
"their work 'Robust JPEG Image Steganography Using Wavelet Domain SVD'" \
"and Adaptive QIM."

EPILOG= "Below are some examples of how to use the program:\n" \
"python SVDAdaptiveQimSteg.py -i image.jpg -m Text.txt\n" \
"    - Embed contents of Text.txt into image.jpg with default options\n" \
"python SVDAdaptiveQimSteg.py -i image.jpg -m Text.txt -b 8 -Tmin 50 -Tmax 100\n" \
"    - Embed Text.txt using blocksize 8, Tmin of 50, and a Tmax of 100\n" \
"python SVDAdaptiveQimSteg.py -i image.jpg -extract -Tmin 50 -Tmax 100\n" \
"    - Extract stegged message from image.jpg WITHOUT using a Ti key and " \
"defined T values.\n" \
"python SVDAdaptiveQimSteg.py -i image.jpg -extract -Tk image.jpg-Ti.key\n" \
"    - Extract stegged message using Ti key file generated at embedding\n\n" \
"Steg your dreams!!!"

UPDATE_DATE = "26 JUL 2026"
RECENT_CHANGES = "Recent Changes:\n" \
"- Reformatted commandline to be easier to understand and read\n"
# ===================================================================
#               Argparse
# ===================================================================
def get_inputs():
    """
    Function that creates an Argparse parser to gather the arguments
    from the commandline. Checks if arguments are valid or not, and
    prints the help statement and all errors if any are found. 
    Returns all values received from parsing commandline arguments.
    """
    # Parser and argument setup
    parser = argparse.ArgumentParser(
        prog="python SVDAdaptiveQimSteg.py",
        description=DESC,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
        )

    parser.add_argument(
        "-i",
        "--image",
        required=True,
        help="path of JPEG image you wish to embed/extract into/from."
    )

    parser.add_argument(
        "-m", 
        "--messagepath", 
        help="The path to the message you wish to embed"
    )
    
    parser.add_argument(
        "-extract",
        "--extract",
        action="store_true",
        help="Extract message from chosen image."
    )

    parser.add_argument(
        "-Tk",
        "--Tikeypath",
        help="Path to Ti Key file for use at extraction. If not specified, " \
        "the no key file will be used."
    )

    parser.add_argument(
        "-Tmin",
        "--Tmin",
        type=int,
        help="Specified value for Tmin to use for embedding or extraction."
    )

    parser.add_argument(
        "-Tmax",
        "--Tmax",
        type=int,
        help="Specified value for Tmax to use for embedding or extraction."
    )

    parser.add_argument(
        "-b",
        "--blocksize",
        type=int,
        help="The size of blocks that LL band will be divided into. " \
        "Default is 4. Increasing lowers capacity, decreasing increases."
    )

    parser.add_argument(
        "-w",
        "--wavelet",
        help="The string of the wavelet to use in the Stationary Wavelet " \
        "Transforms. Default is 'haar'. \n" \
        "Wavelet options: 'haar', 'db2', 'db4', 'sym4', 'bior1.1', 'bior4.4'"
    )
    
    parser.add_argument(
        "-nt",
        "--noTis",
        action="store_true",
        help="Do not create a Ti key file for use at extraction. " \
        "NOTE: This *could* have some impact on data intregity at " \
        "extraction. Will require 32-bit size prepended to front of message."
        )
    
    parser.add_argument(
        "-o",
        "--outputpath",
        help="Chosen path to output extracted data or stego image to."
        )

    # Parse the args
    args = parser.parse_args()
    imagepath : str = args.image
    messagepath : str = args.messagepath
    mode_extract : bool = args.extract
    Tmin : int = args.Tmin
    Tmax : int = args.Tmax
    Tikeypath : str = args.Tikeypath
    blocksize : int = args.blocksize
    wavelet : str = args.wavelet
    mode_noTis : bool = args.noTis
    outputpath : str = args.outputpath
    total_args = len(sys.argv) - 1 # 1 is the source file, subtract that
    
    # Check all inputs are valid via a variety of checks
    errors = []
    # Arg number checks
    if total_args < 2:
        errors.append("Not enough args specified. At least an image and a " \
        "-m <messagepath> or -e for extraction are required") 
    elif total_args > 14:
        errors.append("Too many arguments specified.")

    # Check that image is given, a valid file, valid JPEG, and a valid file. 
    if imagepath is None:
        errors.append("A path to an JPEG image file was not given.")
    elif not os.path.exists(imagepath):
        errors.append("Path to JPEG image file is not valid.")
    elif not is_jpg(imagepath):
        errors.append("Provided image file is not a JPEG.")
    elif os.path.getsize(imagepath) == 0:
        errors.append("Provided image file is empty")

    # Check that messagepath is given, path exists, and that both extract
    # mode and steg more are active at the same time.
    if messagepath is None:
        if not mode_extract:
            errors.append("No action is specified. Please select only one " \
            "option: -m <message> to embed; -e to extract a messsage")
    elif not os.path.exists(messagepath):
        errors.append("Provided path to message data is not valid.")
    elif messagepath is not None and mode_extract:
        errors.append("Both embedding and extraction were chosen. Please " \
        "select only one option: -m <message> to embed; -e to extract a " \
        "message")

    # Check Ti Key path is valid
    if Tikeypath is not None and not mode_extract:
        errors.append("-Tk cannot be used with embedding (-m).")
    if Tikeypath is not None and not os.path.exists(Tikeypath):
        errors.append("Provided path to Ti key is not valid.")

    # Check if T values make sense
    if Tmin is None:
        Tmin = DEFAULT_T_MIN
    elif Tmin < T_MIN_MIN:
        errors.append(f"Provided Tmin is lower than acceptable Tmin of " \
        f"{T_MIN_MIN}.")
    if Tmax is None:
        Tmax = DEFAULT_T_MAX
    elif Tmax < T_MAX_MIN:
        errors.append(f"Provided Tmax is lower than acceptable Tmax of " \
        f"{T_MAX_MIN}.")
    if Tmax <= Tmin:
        errors.append("Provided Tmax is less than or equal to provided " \
        f"Tmin {Tmin}")
    elif Tmin >= Tmax:
        errors.append("Provided Tmin is more than or equal to provided " \
        f"Tmax {Tmax}")

    # Check block size
    if blocksize is None:
        blocksize = DEFAULT_BLOCKSIZE
    elif blocksize < MIN_BLOCKSIZE:
        errors.append(f"Provided blocksize is lower than acceptable " \
        f"min of {MIN_BLOCKSIZE}")
    elif blocksize > MAX_BLOCKSIZE:
        errors.append(f"Provided blocksize is greater than acceptable " \
        f"max of {MAX_BLOCKSIZE}")       
    if not check_dims_with_blocksize(imagepath, blocksize):
        errors.append("Provided image cannot be broken down evenly into " \
        f"provided blocksize of {blocksize}.")

    # Check Wavelet is approved
    if wavelet is None:
        wavelet = DEFAULT_WAVELET
    elif wavelet not in APPROVED_WAVELETS:
        errors.append(f"Selected wavelet '{wavelet}' is not an approved " \
        "wavelet to use.")

    # Print the erros underneath the help message. Helps make it more clear
    # what the actual problem is.
    if errors:
        parser.print_help()
        print("\nThe following errors with your input were found:")
        for error in errors:
            print(f"- {error}")
        print()
        exit()

    # All is good, return data to main
    else:
        return imagepath, messagepath, mode_extract, Tmin, Tmax, Tikeypath, blocksize, wavelet, mode_noTis, outputpath


# ===================================================================
#               Functions
# ===================================================================
def is_jpg(imagepath):
    """
    Function that checks if a given image is a JPEG.
    Returns true or false.
    """
    try: 
        img = Image.open(imagepath)
        if img.format.lower() == "jpeg":
            return True
        else:
            return False
            
    except Exception as e:
        print(f"[-] Error when testing image is a JPG: {e}")
        return False


# -------------------------------------------------------------------
def check_dims_with_blocksize(imagepath, blocksize):
    """
    Helper function that checks if the number of blocks fits
    evenly into the image. Probably not necessary if message 
    won't use entire capacity, but whatever.
    """
    try: 
        img = Image.open(imagepath)
        height, width = img.size
        if height % blocksize == 0 and width % blocksize == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"[-] Error when testing image for acceptable blocksize: {e}")
        return False

    
# -------------------------------------------------------------------
def print_intro_info():
    """
    Function that prints the introduction information for the 
    program. This does NOT include the help information. That gets
    printed separately and is handled exclusively by the argparse 
    library.
    """
    print("\n" \
        "Robust JPEG Image Steganography Using Wavelet Domain SVD" \
        "and Adaptive QIM algorithm implementation.")
    print("This program was written by Nicholas Winkelmann.\n")
    print(f"Most recent update: {UPDATE_DATE}")
    print(RECENT_CHANGES)
    print("========================================================")

# ===================================================================
#               Main
# ===================================================================
def main():
    """
    Main function, gets the command line args, and if they are 
    acceptable, calls the respective embed or extract functions.
    Prints the time each embedding or extraction action took at
    success.
    """
    # Get the args
    imagepath, messagepath, mode_extract, Tmin, Tmax, Tikeypath, blocksize, wavelet, mode_noTis, outputpath = get_inputs()

    # Print Introduction information if all inputs are valid
    print_intro_info()
    time.sleep(1)

    # Either Embed or Extract
    start_time = time.time()
    if mode_extract:
        action = "Extraction"
        extract(imagepath, Tmin, Tmax, Tikeypath, blocksize, wavelet, outputpath)

    else:
        action = "Embedding"
        embed(imagepath, messagepath, Tmin, Tmax, blocksize, wavelet, mode_noTis, outputpath)
    end_time = time.time()

    # Print time
    print(f"[+] {action} completed in {end_time - start_time}s.")

if __name__ == "__main__":
    main()

# EOF
