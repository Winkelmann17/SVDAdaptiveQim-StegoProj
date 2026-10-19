"""
Author: Winkelmann17, Team 22
Team Members: Winkelmann17, Awesome Partner
Purpose: Implementation of the the JPEG steganography algorithm 
presented by Jing Liu, Xiaofeng Song, Guopeng Li, and Kun Han from
their work "Robust JPEG Image Steganography Using Wavelet Domain SVD
and Adaptive QIM."

NOTE: THIS CODE IS AN IMPLEMENTATION OF PRIOR WORK AND RESEARCH. THIS
CODE IS NOT ORIGINAL IN ITS IDEAS OR IMPLEMENTATION. 

Last Updated: July 26 2026
Recent Changes:
- Added NoTis option functionality
- Added output filepath functionality
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
DEFAULT_FILENAME = "stego.jpg"
INT_BIT_SIZE = 32

# Prep message function
def prep_message(messagepath, h, w, mode_noTis, blocksize):
    """
    Function that loads message data and prepends the appropriate 32-bit
    size. If no Ti key is being created. Calculates the capacity from the
    blocksize and image properties.
    Returns full_message to embed, full_length of the message, and the
    capacity.
    """
    # Open chosen message file and get the bits of the file
    print("[+] Loading Message Data...")
    with open(messagepath, "rb") as f:
        contents = bytearray(f.read())
        data_bits = "".join(format(byte, "08b") for byte in contents)
    print(f"[+] Loaded {len(data_bits)} bits of data from the message")

    # Get the length of the bitstring to prepend the size in 32 bits
    if mode_noTis:
        message_length_bits = "".join(format(len(data_bits), "08b"))
        while len(message_length_bits) < INT_BIT_SIZE:
            message_length_bits = "0" + message_length_bits
        full_message = message_length_bits + data_bits
        print("[+] Message prepended with its 32-bit size because no Tis key file will be generated.")
    else:
        full_message = data_bits

    # Inform user if chosen cover image can hold all of the chosen 
    # message or not.
    capacity = (h * w)  // (blocksize * blocksize)
    full_message_length = len(full_message)
    print(f"[+] Pixel dimensions: {h}x{w} = {capacity} blocks => {capacity} bit, {capacity / 8} byte capacity.")
    print(f"    - Length of full message = {full_message_length} bits, {full_message_length / 8} bytes.")
    if full_message_length > capacity:
        print("[*] Chosen message exceeds capacity of chosen cover image. " \
        "As much information will be stegged as possible.")

    return full_message, full_message_length, capacity


# -------------------------------------------------------------------
# Main function
def embed(imagepath, messagepath, Tmin, Tmax, blocksize=4, wavelet="haar", mode_noTis=False, outputpath=None):
    """
    Main function of this file. Called by SVDAdaptiveQimSteg.py. Performs 
    the entire embedding algorithm step-by-step. Made in one large function
    for easy review and analysis. Performs SWTs, Block division, Wi 
    calculations, Ti calculations, SVD on each block, and Singular value
    embedding. When all is complete, the blocks are reconstructed into the
    LL band and then remade into a JPEG of 75 Quality and written to disk
    at the location (if one is specified).
    """
    # Open, convery to GS if needed, put data in a np array
    with Image.open(imagepath) as img:
        img_data = np.array(img.convert("L"))
    shape = img_data.shape
    height, width = shape


    # Showing user the options that are being used
    print("[+] Beginning embedding with the following core options:")
    print(f"    - Tmin: {Tmin}")
    print(f"    - Tmax: {Tmax}")
    print(f"    - blocksize: {blocksize}")
    print(f"    - wavelet: {wavelet}")


    # Prepping the message
    final_message, full_length, capacity = prep_message(messagepath, height, width, mode_noTis, blocksize)


    # Stationary Wave Transform of image data
    coeffs = pywt.swt2(img_data, wavelet, level=1, norm=True)
    LL_band, (LH_band, HL_band, HH_band) = coeffs[0]
    print("[+] Stationary wavelet transform complete.")

    
    # Split LL band into blocks
    blocks = []
    for i in range(0, height, blocksize):
        for j in range(0, width, blocksize):
            blocks.append(LL_band[i:i+blocksize, j:j+blocksize])
    print(f"[+] LL band separated into {capacity} {blocksize}x{blocksize} blocks.")


    # Calculate Wi for each block to get Wmax and Wmin for equations
    wis = []
    wmax = 0
    wmin = 0

    # Iterate through each block calculating average and standard 
    # standard deviation to order to caluclate the Wi. Needed to 
    # calculate the quantization step Ti later.
    print("[+] Beginning Wi calculations...")
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


    # SVD, Ti, and Embedding Loop
    Tis = []
    print("[+] Performing SVD, Ti calcs, and embedding on each block...")
    for i in range(capacity):
        # break if the message length has been met,
        # no further stegging necessary
        if i > full_length - 1:
            break
        elif i == full_length // 4:
            print("    - Embedding 25% complete...")
        elif i == full_length // 2:
            print("    - Embedding 50% complete...")
        elif i == (full_length * 3) // 4:
            print("    - Embedding 75% complete...")
        # Ti Calculation
        # NOTE: Paper had an unfortunate typo, equation really is T_MAX - ...
        Ti = Tmax - (Tmax - Tmin) * ((wis[i] - wmin)/(wmax - wmin))
        Tis.append(Ti)

        # SVD each block and pull the largest singular value for
        # modification.
        U_mat, S_mat, Vh_mat = np.linalg.svd(blocks[i])
        largest_s = S_mat[0]
        mi = int(final_message[i])

        # Modify the largest singular value. Split equation up so it is
        # easy to read, honestly could've done it more.
        part1 = np.floor(largest_s/Ti)
        part2 = np.mod(np.floor((largest_s/Ti) + mi), 2)
        new_s = (part1 + part2) * Ti

        # Create new block with modified largest singular value
        S_mat[0] = new_s
        S_mat_modified = np.diag(S_mat)

        # Performing Matrix multiplication to undo the SVD.
        # NOTE: Matrix Multiplication is NOT COMMUTATIVE. 
        # Very important to do it in this order.
        part1 = np.matmul(U_mat, S_mat_modified)
        modified_block = np.matmul(part1, Vh_mat)
        blocks[i] = modified_block

    print("[+] All blocks modified.")
    print(f"    - Sneak peek of embedded bits: {final_message[:24]}...")


    # Embedding complete, shove modified blocks into newly formed
    # LL band in order to create new stego image
    new_LL_band = np.zeros(shape)
    index = 0
    for i in range(0, height, blocksize):
        for j in range(0, width, blocksize):
            new_LL_band[i:i+blocksize, j:j+blocksize] = blocks[index]
            index += 1
    print("[+] New LL band created from modified blocks.")


    # Inverse Stationary Wave Transform, puts image data back in 
    # normal domain for re-introducing into a new stego image.
    # Keeps the other bands from the original image, as only 
    # the LL band was changed.
    coeffs[0] = new_LL_band, (LH_band, HL_band, HH_band)
    stego_img_data = pywt.iswt2(coeffs, wavelet, norm=True)
    print("[+] Inverse stationary wavelet transform complete.")

    
    # Ensure stego image data meets criteria of bytes in an image
    corrected_stego_data = np.clip(stego_img_data, 0, 255)
    corrected_stego_data = corrected_stego_data.astype(np.uint8)
    print("[+] Stego image data corrected to fit byte values.")


    # Finally, save the image to disk with the default or chosen
    # output name. 
    stego_img = Image.fromarray(corrected_stego_data)
    try:
        stego_img.save(outputpath, quality=75, subsampling=0)
    except Exception as e:
        print(f"[-] Error when saving file: {e}")
        outputpath = DEFAULT_FILENAME
        stego_img.save(outputpath, quality=75, subsampling=0)


    # Save Tis to disk if that option was chosen
    if not mode_noTis:
        Ti_data = pickle.dumps(Tis)
        try:
            keyfile = f"{outputpath}-Ti.key"
            f = open(keyfile, "wb")
            f.write(Ti_data)
            print(f"[+] Ti key file was written to disk at {keyfile}")
            f.close()
        except Exception as e:
            print(f"[-] Error occurred when writing Ti data to disk: {e}")


    # Final message
    print(f"[+] Stego image saved and written to: {outputpath}.")

# EOF
