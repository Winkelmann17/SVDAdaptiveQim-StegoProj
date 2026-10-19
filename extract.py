"""
Author: Winkelmann17, Team 22
Team Members: Winkelmann17, Awesome Partner
Purpose: Implementation of the the JPEG steganography algorithm 
presented by Jing Liu, Xiaofeng Song, Guopeng Li, and Kun Han from
their work "Robust JPEG Image Steganography Using Wavelet Domain SVD
and Adaptive QIM."

NOTE: THIS CODE IS AN IMPLEMENTATION OF PRIOR WORK AND RESEARCH. THIS
CODE IS NOT ORIGINAL IN ITS IDEAS OR IMPLEMENTATION. 

Last Updated: July 25 2026
Recent Changes:
- Added Ti key file functionality
- Added correct output path functionality
- Added changing Tmin, Tmax, blocksize, and wavelet functionality
"""
# Imports
import numpy as np
import pickle
from PIL import Image
import pywt

# Constants
W_AVE = 1.5221
W_STD = 4.8824
INT_BIT_SIZE = 32


# Main function
def extract(imagepath, Tmin, Tmax, Tikeypath, blocksize, wavelet, outputpath):
    """
    Main function of this file. Called by SVDAdaptiveQimSteg.py. Performs the
    entire extraction part of the algorithm. Made in one large function for 
    easy review and analysis. Performs SWT, block division, SVD, Singular 
    value extraction, and bit extraction. Then, reconstructs message into 
    a bit string before writing to designated output file (if specified).
    Capable of working with a Ti key as paper specified, or without one.
    """
    # Open the image and pull the data into a np array
    print("[+] Beginning extraction...")
    with Image.open(imagepath) as img:
        img_data = np.array(img.convert("L")) # Not needed?
    shape = img_data.shape
    height, width = shape
    print(f"[+] Image data loaded from {imagepath}.")


    # Showing user the options that are being used
    print("[+] Beginning extraction with the following core options:")
    if Tikeypath is None:
        print(f"    - Tmin: {Tmin}")
        print(f"    - Tmax: {Tmax}")
    else:
        print(f"    - Ti values in {Tikeypath}")
    print(f"    - blocksize: {blocksize}")
    print(f"    - wavelet: {wavelet}")


    # Perform Stationary Wavelet Transform on image data and 
    # extract LL band
    coeffs = pywt.swt2(img_data, wavelet, level=1, norm=True)
    LL_band, (LH_band, HL_band, HH_band) = coeffs[0]
    print("[+] Stationary wavelet transform complete.")


    # Split LL band into blocks
    blocks = []
    for i in range(0, height, blocksize):
        for j in range(0, width, blocksize):
            blocks.append(LL_band[i:i+blocksize, j:j+blocksize])
    capacity = len(blocks)
    print(f"[+] LL band separated into {capacity} {blocksize}x{blocksize} blocks. ")
    print(f"    - Total capacity is equal to the number of blocks: {capacity} bits, {capacity/8} bytes.")


    # Check if Tikeypath is a valid keyfile, if not, just run as if
    # one was not provided, by calculating each Wi to calculate each Ti.
    if Tikeypath is not None:
        try:
            f = open(Tikeypath, "rb")
            data = f.read()
            f.close()
            Tis = pickle.loads(data)
            print(f"[+] Loaded Ti key file: {Tikeypath}")
        except Exception as e:
            print(f"[-] Could not load Tis from key file: {e}")
            print("    - Will run as if no key file was provided.")
            Tikeypath =  None


    # Calculate Wi for each block to get Wmax and Wmin for equations
    # These values should be different than the ones from the original
    # image.
    extracted_message = ""
    if Tikeypath is None:
        wis = []
        wmax = 0
        wmin = 0

        # Iterate through each block calculating average and standard 
        # standard deviation to order to caluclate the Wi. Needed to 
        # calculate the quantization step Ti later.
        print("[+] No Ti key file provided -> Beginning Wi calculations...")
        for i in range(capacity):
            # Progress updates
            if i == capacity // 4:
                print("    - Wi calculations 25% complete...")
            elif i == capacity // 2:
                print("    - Wi calculations 50% complete...")
            elif i == (capacity * 3) // 4:
                print("    - Wi calculations 75% complete...")

            ave = np.mean(blocks[i])
            std = np.std(blocks[i])
            wi = W_AVE * ave + W_STD * std 
            wis.append(wi)
        wmax = np.max(wis)
        wmin = np.min(wis)
        print("[+] Wi's calculated from all blocks.")
        print(f"    - Wmax={wmax} ; Wmin={wmin}")


        # Perform SVD, calculate Ti, and extract the first 32-bits
        # which are the embedded size of the actual message. Pulling
        # this value, tells the extraction algorithm when the entire 
        # message has been extracted.
        print(f"[+] Performing SVD and extracting the {INT_BIT_SIZE}-bit message length value.")
        size_in_bits = ""
        for i in range(INT_BIT_SIZE):

            # Ti Calculation
            # NOTE: Paper had an unfortunate typo, equation really is T_MAX - ...
            Ti = Tmax - (Tmax - Tmin) * ((wis[i] - wmin)/(wmax - wmin))

            # SVD each block and pull the largest singular value for 
            # extraction equation. Other values pulled from SVD are
            # not used in the extraction since no rebuilding of blocks
            # is necessary.
            U_mat, S_mat, Vh_mat = np.linalg.svd(blocks[i])
            largest_s = S_mat[0]
            extracted_size_bit = int(np.mod(np.round(largest_s/Ti), 2))
            size_in_bits += str(extracted_size_bit)

        # Size is finished being extracted, now can be used to get the rest
        # of the message.
        message_length = int(size_in_bits, 2)
        print("[+] Message length extraction complete.")
        print(f"    - Message length is {message_length} bits, {message_length / 8} bytes.")


        # Perform SVD, calculate Ti, and extract bits up until the message
        # length is achieved. Starts at INT_BIT_SIZE to ensure no data
        # is missed from searching for the length bits.
        print(f"[+] Performing SVD and extraction on remaining {message_length} blocks containing message data.")
        for i in range(INT_BIT_SIZE, capacity):     # break at capcacity
            # Break when message length is met (if not corrupted)
            if i > message_length + INT_BIT_SIZE - 1:
                break
            elif i == message_length // 4:
                print("    - Extraction 25% complete...")
            elif i == message_length // 2:
                print("    - Extraction 50% complete...")
            elif i == (message_length * 3) // 4:
                print("    - Extraction 75% complete...")


            # Same Ti calculation, nothing new here
            Ti = Tmax - (Tmax - Tmin) * ((wis[i] - wmin)/(wmax - wmin))

            # SVD each block and pull the largest singular value for 
            # extraction equation.
            U_mat, S_mat, Vh_mat = np.linalg.svd(blocks[i])
            largest_s = S_mat[0]
            extracted_mi = int(np.mod(np.round(largest_s/Ti), 2))
            extracted_message += str(extracted_mi)


    # Extract with Ti key file, no extra calculations are necesasry
    else:
        # Message length is the number of Tis calculated at embedding
        print("[+] Extracting with Ti key file")
        message_length = len(Tis)
        for i in range(len(Tis)):
            Ti = Tis[i]
            U_mat, S_mat, Vh_mat = np.linalg.svd(blocks[i])
            largest_s = S_mat[0]
            extracted_mi = int(np.mod(np.round(largest_s/Ti), 2))
            extracted_message += str(extracted_mi)

    # Print that extraction is complete
    print("[+] Bit extraction from Singular values complete.")
    print(f"    - Sneak peek of extracted bits message: {extracted_message[:24]}...")


    # Convert the string of bits into actual writeable bytes.
    # Convert to integers, convert to bytes, ensure big endian format
    val = int(extracted_message, 2)
    extracted_bytes = val.to_bytes((val.bit_length() + 7) // 8,"big")

    # Create output file name if one is not made.
    if outputpath is None:
        outputpath = f"{imagepath}-ext.txt"
    # Write bytes to output file
    try:
        f = open(outputpath, "wb")
        f.write(bytes(extracted_bytes))
        f.close()
    except Exception as e:
        print(f"[-] Error when saving extracted data to disk: {e}")
        with open(f"{imagepath}-ext.txt", "wb") as f:
            f.write(bytes(extracted_bytes))

    print(f"[+] Extracting message data wrote to {outputpath}.")

# EOF
