import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from PIL import Image
from skimage import io
from skimage.metrics import structural_similarity as ssim
matplotlib.use('Agg')


def determine_psnr(original_image_path, encoded_image_path):
    # Load the original and edited images
    original_img = cv2.imread(original_image_path)
    edited_img = cv2.imread(encoded_image_path)

    # Convert the images to float32 data type
    original_img = original_img.astype(np.float32)
    edited_img = edited_img.astype(np.float32)

    # Calculate the mean squared error (MSE) between the original and edited images
    mse_R = np.mean((original_img[:, :, 0] - edited_img[:, :, 0]) ** 2)
    mse_G = np.mean((original_img[:, :, 1] - edited_img[:, :, 1]) ** 2)
    mse_B = np.mean((original_img[:, :, 2] - edited_img[:, :, 2]) ** 2)
    mse = (mse_R + mse_G + mse_B) / 3

    # Calculate the maximum pixel value
    max_pixel_value = 255

    # Calculate the PSNR using the formula PSNR = 20 * log10(max_pixel_value / sqrt(MSE))
    psnr = 20 * np.log10(max_pixel_value / np.sqrt(mse))

    return psnr                 # unit is dB

def determine_pvd(original_image_path, encoded_image_path):
    # Load the original and encoded image
    original_img = cv2.imread(original_image_path)
    encoded_img = cv2.imread(encoded_image_path)
    
    # compute the mean squared error (MSE) between the original and edited images for all channels
    mse = np.mean((original_img.astype(np.float32) - encoded_img.astype(np.float32)) ** 2)
    
    filename = encoded_image_path.replace('images', 'plots')
    filename = filename.replace('modified.jpg', 'histogram.jpg')

    return mse*0.5 , filename                              # mean absolute difference


def plot_histograms(original_image_path, encoded_image_path):
    # Load the original and encoded image
    original_img = cv2.imread(original_image_path)
    encoded_img = cv2.imread(encoded_image_path)

    # Split the channels of the original and encoded images
    original_b, original_g, original_r = cv2.split(original_img)
    encoded_b, encoded_g, encoded_r = cv2.split(encoded_img)
    
    # Plot the histograms of the pixel values in each channel
    fig, axs = plt.subplots(2, 3, figsize=(12, 6))
    colors = ['R', 'G', 'B']

    for i, channel in enumerate([original_b, original_g, original_r]):
        axs[0, i].hist(channel.flatten(), bins=256,
                       range=(0, 256), color='blue', alpha=0.5)
        axs[0, i].set_xlim([0, 256])
        axs[0, i].set_ylim([0, 10000])
        axs[0, i].set_title('Original Image - Channel ' + colors[i])

    for i, channel in enumerate([encoded_b, encoded_g, encoded_r]):
        axs[1, i].hist(channel.flatten(), bins=256,
                       range=(0, 256), color='green', alpha=0.5)
        axs[1, i].set_xlim([0, 256])
        axs[1, i].set_ylim([0, 10000])
        axs[1, i].set_title('Encoded Image - Channel ' + colors[i])

    # Save the figure as an image
    filename = encoded_image_path.replace('images', 'plots')
    filename = filename.replace('modified.jpg', 'histogram.jpg')
    
    # ensure that the plots folder exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    fig.savefig(filename)
    plt.close(fig)


def determine_ssim_values(original_image_path, encoded_image_path):
    # Load the original and encoded images
    original_img = io.imread(original_image_path)
    encoded_img = io.imread(encoded_image_path)

    # Compute the SSIM for each color channel
    ssim_r = ssim(original_img[:, :, 0],
                  encoded_img[:, :, 0], multichannel=False)
    ssim_g = ssim(original_img[:, :, 1],
                  encoded_img[:, :, 1], multichannel=False)
    ssim_b = ssim(original_img[:, :, 2],
                  encoded_img[:, :, 2], multichannel=False)
    ssim_avg = (ssim_r + ssim_b + ssim_g) / 3

    return ssim_r, ssim_g, ssim_b, ssim_avg


def determine_bpp(compressed_image_path):

    # Load the image using OpenCV
    image = Image.open(compressed_image_path)

    # Get the size of the image
    width, height = image.size

    # Calculate the number of bits per pixel
    bpp = os.path.getsize(compressed_image_path) * 2 / (width * height)

    return bpp
    
    # original_image = Image.open(original_image_path)
    # compressed_image = Image.open(compressed_image_path)

    # # access the image data as a NumPy array to get the shape
    # original_array = np.array(original_image)
    # stego_array = np.array(compressed_image)

    # # calculate the number of pixels in each image using the NumPy array's shape
    # original_pixels = original_array.shape[0] * original_array.shape[1]
    # stego_pixels = stego_array.shape[0] * stego_array.shape[1]

    # # calculate the total number of bits in each image.
    # original_bits = original_image.dtype.itemsize * 8 * original_pixels
    # stego_bits = compressed_image.dtype.itemsize * 8 * stego_pixels

    # # calculate the bpp of each image.
    # original_bpp = original_bits / original_pixels
    # stego_bpp = stego_bits / stego_pixels

    # return stego_bpp