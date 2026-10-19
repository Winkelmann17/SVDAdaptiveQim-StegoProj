
# SVDAdaptiveQimSteg.py Guide
This document serves as a guide for using the SVDAdaptiveQimSteg.py tool created by Team 22 for the CS 5XXX Steganography Project. This document has 5 main sections:
1. Overview of Algorithm
2. General Use of SVDAdaptiveQimSteg.py
3. Specific Examples
4. Provided Files
5. Important Notes and Findings
  
Please read all sections to understand how to use this program, and its limitations.

# Disclaimer!
This project and report were generated in an academic environment. This project is not meant to obtain any profit or be used in any official manner. 

# Overview of Algorithm
The paper can be found here: https://ieeexplore.ieee.org/document/10270839

This program was designed as an implementation of Jing Liu et. al's work "Robust JPEG Image Steganography Using Wavelet Domain SVD and Adaptive QIM." The aim of their algorithm was to produce a *robust* steganography algorithm that can persist through further JPEG compression and distortion. Robustness was the primary goal, not necessarily perfect extraction.
  
The main, general concept of the algorithm revolves around performing mathematical transforms and matrix math to isolate certain values that can hold a bit parity. This parity can be rediscovered (to a reasonable extent anyway) through the same operations at extraction. These values are expected to reasonably hold their value/parity after further compression. 
  
The general flow of embedding is this:
```
INPUT : Acceptable JPEG image
    1. Perform Stationary Wavelet Transform on image data
    2. Extract LL subband from data (low frequency subband)
    3. Split LL subband into blocks (4x4 in the paper)
    4. Perform SVD on each block and isolate the Singular values
    5. Calculate a Quantization step, Ti, for embedding. 
        **Save these values in a keyfile**

    -------- Embedding happens here -----------------------------
   **6. Modify the singular values based on mathematical equations
        to store bits

    -------- Reconstruction begins here -------------------------
    7. Reconstruct the block with modified singular value via 
        reverse SVD (matrix multiplication)
    8. Reform the LL subband from the modified blocks
    9. Perform Inverse Stationary Wavelet Transform to create new
        image data
OUTPUT: STEGO JPEG image, Ti keyfile
```

For extraction, the algorithm follows the same steps as the first half of the 
previous flow, simply stopping at extracting the message bits from the 
Singular values:
```
INPUT: Stego JPEG, Ti keyfile
    1. Perform Stationary Wavelet Transform on image data
    2. Extract LL subband from data (low frequency subband)
    3. Split LL subband into blocks (4x4 in the paper)
    4. Perform SVD on each block and isolate the Singular values

    ----------- Extraction happens here --------------------------
    5. Using Ti values from keyfile, perform mathematical operations to extract
        the message bits from the Singular values.

    6. Save message bits in whatever format is desired
OUTPUT: Message
```

The Python code that accompanies this readme performs those embedding and extraction steps with a few more tweaks which are noted in the section called Important Notes and Findings.


# General Use of SVDAdaptiveQimSteg.py
```
usage: python SVDAdaptiveQimSteg.py [-h] -i IMAGE [-m MESSAGEPATH] [-extract] 
            [-Tk TIKEYPATH] [-Tmin TMIN] [-Tmax TMAX] [-b BLOCKSIZE] [-w WAVELET] 
            [-nt] [-o OUTPUTPATH]
To run the program's help function simply run:
    > python SVDAdaptiveQimSteg.py -h
This will show all the options including how to specify between embedding and 
extraction modes.

To embed, simply run:
    > python SVDAdaptiveQimSteg.py -i <path/to/image.jpg> -m <path/to/message/file>
This will embed the contents of the file passed with the -m option into the 
specified JPEG file. The outputs will be the stego.jpg file and the Ti key file, 
simply named <output_filename>-Ti.key

To extract, simply run:
    > python SVDAdaptiveQimSteg.py <path/to/stego.jpg> -e -Tk <path/to/stego.jpg-Ti.key>
This will extract the contents of the the stego file utilizing the Ti key file generated
at embedding. *Using the Ti key file is the most accurate way to extract messages*
```
### Required Options and Flags
Below are all the **required** arguments for the program labeled by their associated mode:
``` 
MODE: ALL
-i, --image                   <REQUIRED>
    This is the path for image to embed or extract from. Must be a valid JPEG.

MODE: Embedding
-m, --messagepath           <REQUIRED FOR EMBEDDING>
    This option is the path to the mesasge file. It can be any file that is not empty.
    Text files, small PNGs, and small MP3s were all being used and tested.

MODE: Extracting
-extract, --extract            <REQUIERD FOR EXTRACTION>
    This option designates that the image file will be extracted from, rather than 
    embedded into.
    This option is a flag, no additional data required. 
```

### Optional Options and Flags
Below are all the *required* arguments for the program labeled by their associated mode:
```
MODE: Embedding
-nt, --noTis
    This option skips generating the Ti key file, as it is *technically* not necessary, 
    more will be expanded on this in the Important Notes and Findings section.
    Using this option will prepend your messagebits with 32-bits designated the size 
    of the embedded message.
    This option is a flag, no additional data required.

MODE: Extraction
-Tk, --Tikeypath
    This option specifies the path to the Ti key file, so that the Tis can be loaded 
    for use in the extraction operations.
    If selected any -Tmin or -Tmax options will be ignored. 
    If not provided, the algorithm will simply recalculate the Tis for each block, 
    starting with the 32-bit message length to get payload size.

MODE: ALL
-Tmin, --Tmin
    This option specifies what value to use for Tmax in the Ti equations.
    Increasing this value can make the extraction more accurate and robust.
    Must never be below the accepted min of 20 in the paper, or be equal or more than Tmax.

MODE: ALL
-Tmax, --Tmax
    This option specifies what value to use for Tmax in the Ti equations. 
    Increasing this value can make the extraction more accurate and robust. 
    Must never be below the accepted max of 70 in the paper, or be equal or less than Tmin.

MODE: ALL
-b, --blocksize
    This option changes the blocksize from the default of 4 to whatever is specified.
    Min is 2, Max is 64. Increasing the block size, reduces capacity GREATLY, while reducing 
    blocksize increases capacity.
    Default is 4.

MODE: ALL
-w, --wavelet
    This option specifies what Stationary Wavelet Transform to use in pywt's swt and iswt 
    functions. Jing Lie et al. never specify what transform they used, so options are given 
    to the user if they wish.
    Defaults to "haar." Has some impact on performance. 
    ***MUST MATCH ON EXTRACTION***

MODE: ALL
- o, --outputpath
    This option HOPEFULLY is self-explanatory. Allows you to define the output filename and path.
    If a bad name or path is given, program uses the defaults.
```


# Specific Examples

1. Embedding a text file named apples.txt into pie.jpg without creating a Ti key:
    > python SVDAdaptiveQimSteg.py -i pie.jpg -m apples.txt -nt
  
2. Embedding a text file named apples.txt into pie.jpg with a blocksize of 8, sym4 wavelet, and 
output named epic.jpg:
    > python SVDAdaptiveQimSteg.py -i pie.jpg -m apples.txt -b 8 -w sym4 -o epic.jpg
  
3. Embedding a text file named apples.txt into pie.jpg with a Tmin of 50 and a Tmax of 100
    > python SVDAdaptiveQimSteg.py -i pie.jpg -m apples.txt -Tmin 50 -Tmax 100
  
4. Embedding a text file named apples.txt into pie.jpg using the sym4 wavelet
    > python SVDAdaptiveQimSteg.py -i pie.jpg -m apples.txt -w sym4
  
5. Extracting a message from pie.jpg into a file named output.txt with a Ti key
    > python SVDAdaptiveQimSteg.py -i pie.jpg -extract -Tk pie.jpg-Ti.key -o output.txt
  
6. Extracting a message from pie.jpg into a file named bunny.mp3 with NO Ti key, Tmins and Tmaxs 
set, a blocksize of 8, and a sym4 wavelet:
    > python SVDAdaptiveQimSteg.py -i pie.jpg -extract -Tmin 100 -Tmax 150 -b 8 -w sym4 -o bunny.mp3


# Provided Files

SVDAdaptiveQimSteg.py 
- entry point for the program. Handles the commandline parsing with Pythons argparse library embed.py
- embedding code called by SVDAdaptiveQimSteg.py
- Contains the entirety of the embedding algorithm and outputs the stego JPEG and Ti keyfile (unless specified otherwise)

extract.py
- extracting code called the by SVDAdaptiveQimSteg.py
- Contains the entirety of the extracting algorithm and outputs the message to a file
- Either uses the Ti keyfile or recalculates all Tis for extraction

requirements.txt
- file that lists all requirements needed for the program
- Can easily install all requirements with pip -r requirements.txt

/Supplemental/QualityConvert.py
- Garbage script that can be done to create new JPEG of a different quality

/BadImages/*
- Images that do not fit SPECIFICALLY the 4x4 block division, program checks for this and will yell at you
- Here only to show that it yells at you without crashing the program. No other reason

/75Grayscale/*
- 75 Quality Grayscale JPEGs for testing. Varying sizes to fit different sized messages
- Paper specifically tested on quality 75 images so those were used here

/FilesToHide/*
- Files that were used as messages for testing embedding and extraction. Varying sizes and types


# Important Notes and Findings From Our Limited Analysis and Implementation
Jing Liu et al. do not specify a lot of key parts of this algorithm in their work.
- Specific SWT/ISWT wavelet not specified
- STCs not substantially documented (excluded from our implementation)
- Specific failures of the algorithm (IE, cartoon images have poor performance)
- File format / method of saving Ti keyfile 
- Specific confines of their experiments including:
    - Length of messages/payloads being embedded
    - Kinds/filetypes of messages being embedded

The algorithm does not achieve 100% extraction rates all the time, but gathers most data. Increasing the Tmin and Tmax value increases the overall Ti value and leads to higher rates of correct extraction, at the cost of higher distortion.
- This effect is easy to see with text as less and less of the test will be extracted incorrectly.
- It is entirely possible that this is really just a fault of bad cover imagesrather than the algorithm itself. 
- **This is not to say that the algorithm doesn't work, it does, this is evident using default options with the FilesToHide/Tank.txt and  75Grayscale/Peacock.jpg which has a 99% extraction success**
- It is possible to embed George.mp3 and Puma.mp3 in 75Grayscale/75Lake.jpg and extract with defaults and using the generated Ti key, though some corruption is evident.
- If extraction is not working, it could be insufficient Tis, or a bad cover image.
- It is possible that because we opted not to implement the STCs portion, this has affected algorithm performance.

The algorithm seems to suffer heavily with cartoon images, or images with large amounts of one solid color.
- 75Grayscale/SecretSquirrel.txt does not perform well at all, it has a large white background
- This generally implies that some images are better than others, which was observed, test messages and cover images for best candidates if using this in a real world scenario

The algorithm takes some time on larger files, it is not a fast algorithm by any means. The time is printed to the screen on each run.  

Extraction performance is generally better when using the Ti key because calculations of Wis are different due to the modified blocks affecting Wi stats.
- It is still possible to extract without using the Ti key as well, but you are entirely at the mercy of changing values

Initial JPEG compression of the stego.jpg at creation seems to hurt the 100% extraction rate. When we performed all algorithm steps, up until creating the new stego image data, when that new image data was instead ran through the extraction algorithm, rather than being written to the stego.jpg, it was seen to be nearly perfectly reversible. This near 100% reversibility is removed after initial JPEG compression when Pillow saves the stego.jpg. 
- Lowering Stego.jpg quality further below 75, still seems to allow for the stego message to be extracted (not 100%), this is consistent with the paper's goals and design.
- Embedding FilesToHide/Tank.txt in 75Grayscale/75Mandy.jpg and then using QualityConvert.py to convert the stego image to 50 quality, the extracted message is largely the same. 

Highly volatile File Types are not great candidates for this method of steganography  

Larger block sizes, tend to be more imperceptible, however this is a massive tradeoff with capacity.
- There do seem to be some upper limits depending on the image. Too largely of a blocksize was seen to prevent correct extraction at times.

Should STCs have been implemented, there would've been greater imperceptibility overall, but they were not due to time constraints and the limits of the speedy summer semester.

---

Written by Winkelmann17  
Last Updated 19 October 2026 for fitness to upload to Github