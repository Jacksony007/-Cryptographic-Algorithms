"""
Adapted from: https://github.com/TejveerSingh13/Image-Steganography/blob/main/Code/histo-shift.py
"""

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pickle
import os
from django.conf import settings

# This function computes the histogram of an 8-bit image.
"""
Parameters:
image (numpy.ndarray): An 8-bit grayscale image

Returns:
x (numpy.ndarray): An array of intensity values from 0 to 255
intensities_array (numpy.ndarray): An array of the frequency of each intensity value
"""
def histogram_8bit(image):
    num_of_bins = 256
    intensities_array = np.zeros(num_of_bins)
    img_hei = image.shape[0]
    img_wid = image.shape[1]
    
    # Iterate through each pixel in the image and increment the appropriate bin.
    for i in range(img_hei):
        for j in range(img_wid):
            pixel = image[i][j] 
            intensities_array[pixel] += 1  

    x = np.arange(num_of_bins)

    return x, intensities_array

# This function takes an 8-bit cover image as input and returns the maximum number of bits that a specific channel can handle
"""
Parameters:
    cover_image: an 8-bit numpy array representing the cover image
"""
def max_data(cover_image):
    # It first verifies that the image is 8-bit and then finds the histogram of pixel intensities in the image
    if cover_image.dtype != "uint8":
        return -1
    intensities = histogram_8bit(cover_image)[1]
    # It then finds the peak point of the histogram to determine the maximum number of bits that can be used for hiding data
    peak_point = np.argmax(intensities)
    # The function returns this maximum number of bits
    return intensities[peak_point]

# Function to encode data
"""
Parameters:
    cover_image: an 8-bit numpy array representing the cover image
    bit_stream: binary data to be encoded in the cover image
"""
def hide_data(cover_image, bit_stream):
    
    # Verify if image is an 8-bit image
    if cover_image.dtype != "uint8":
        return -1
    
    # Find the histogram of the cover image
    bins, intensities = histogram_8bit(cover_image)
    # Find the peak point of the histogram
    peak_point = np.argmax(intensities) 
    
    # Verify if the bit stream can be embedded in the cover image
    size = len(bit_stream)
    if size > intensities[peak_point]:
        return -1
        
    # Shift right histogram values larger than the peak point by 1
    img_hei = cover_image.shape[0]
    img_wid = cover_image.shape[1]
    for i in range(img_hei):
        for j in range(img_wid):
            pixel = cover_image[i][j]
            if pixel > peak_point and pixel < len(bins)-1:
                cover_image[i][j] += 1

    # Hide information
    bit_count = 0
    for i in range(img_hei):
        for j in range(img_wid):
            if bit_count < size:
                if cover_image[i][j] == peak_point:
                    if bit_stream[bit_count] == '1':
                        cover_image[i][j] += 1
                    bit_count += 1
            else:
                break
    return cover_image, peak_point

# Function to decode data
"""
Parameters:
    cover_image: A numpy array representing an 8-bit grayscale image.
    peak_point: An integer representing the peak point of the image's specific channel.
    size: An integer representing the size of the encoded bit stream in a specific channel.
"""
def reveal_data(cover_image, peak_point, size):
    
    # Verify that the image is an 8-bit grayscale image
    if cover_image.dtype != "uint8":
        return -1    
    # Compute the histogram of the cover image
    bins, intensities = histogram_8bit(cover_image)
    img_hei = cover_image.shape[0]
    img_wid = cover_image.shape[1]
    
    # Extract the encoded bit stream from the cover image
    size = int(size)
    bit_count = 0
    bit_stream = []
    for i in range(img_hei):
        for j in range(img_wid):
            if bit_count < size:                
                pixel = cover_image[i][j]
                if pixel == peak_point:
                    bit_stream.append('0')
                    bit_count += 1
                elif pixel == peak_point + 1:
                    bit_stream.append('1')
                    bit_count += 1
            else:
                break
    
    return bit_stream

# Main Encoder Function
def Image_Encoder(img_2_encr, txt_2_encr, output_path):

    # Load the image and spliting the image into its RGB channels
    img = cv2.imread(img_2_encr)

    # Load the image and spliting the image into its RGB channels
    img = cv2.imread(img_2_encr)
    r, g, b = cv2.split(img)

    # Function to encode data in a channel
    def Encoder(data, size, xs, cover):
        content = data[size: size + xs]
        new_size = int(size+xs)
        v, p = hide_data(cover,content)
        return v, p, new_size

    secret_data = txt_2_encr
    num_chars = len(secret_data)

    # Checking the max data that can be encoded
    rs = int(max_data(r))
    gs = int(max_data(g))
    bs = int(max_data(b))
    enc_limit =  rs+gs+bs

    size = 0
    rp = rse = gp = gse = bp = bse = 0
    char_left = num_chars

    if char_left >= rs:
        rse = rs
        r, rp, size = Encoder(secret_data, size, rse, r)
        char_left -= rse
    elif char_left > 0 and (char_left < rs):
        rse =  char_left
        r, rp, size = Encoder(secret_data, size, rse, r)
        char_left -= rse

    if char_left >= gs:
        gse = gs
        g, gp, size = Encoder(secret_data, size, gse, g)
        char_left -= gse
    elif char_left > 0 and (char_left < gs):
        gse =  char_left
        g, gp, size = Encoder(secret_data, size, gse, g)
        char_left -= gse

    if char_left >= bs:
        bse = bs
        b, bp, size = Encoder(secret_data, size, bse, b)
        char_left -= bse
    elif char_left > 0 and (char_left < bs):
        bse =  char_left
        b, bp, size = Encoder(secret_data, size, bse, b)
        char_left -= bse

    # Create a 2D list from the variables
    data = [[rp, rse], [gp, gse], [bp, bse]]
    
    filename = output_path.split('\\')[-1].split('.')[0]
    
    # Construct the file path using os.path.join
    file_path = os.path.join(settings.MEDIA_ROOT, 'lsb', f'{filename}_enc_data.pkl')

    # Make sure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the list to the file
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

    merged = cv2.merge([r, g, b])
    # ensure the output path exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, merged)
    
    return output_path

# Main Decoding function
def Image_Decoder(encr_img, encr_data):

    def Decoder(cover, peak, size):
        bl = reveal_data(cover, peak, size)
        return bl

    bis=[]
    xbs=[]

    # Load the image
    enc_img = cv2.imread(encr_img)
    rd, gd, bd = cv2.split(enc_img)
    channels = [rd, gd, bd]

    # Load the data object from the file using pickle
    with open(encr_data, 'rb') as f:
        data = pickle.load(f)

    for i,d in enumerate(data):
        if (d[0] > 0) and (d[1] > 0) :
            xbs= Decoder(channels[i], d[0], d[1])
            bis.extend(xbs) 
            xbs=[]
    
    return ''.join(bis)