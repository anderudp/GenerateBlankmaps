import cv2
import numpy as np
import numba as nb
import glob
import time
import json
import os
from tqdm import tqdm

superregion = "United States"
area_type = "States"
remove_from_filename = ["2560px-", "_in_United_States.svg"]
area_color = np.array((193, 39, 55)).astype(np.uint8)
bg_filtered_color = np.array((254, 254, 233)).astype(np.uint8)
area_threshold = 2
bg_threshold = 10

save_to = f"{os.path.dirname(os.path.abspath(__file__))}/{superregion}"
images_path = f"{os.path.dirname(os.path.abspath(__file__))}/*.png"


@nb.njit
def pixel_color_distance(pxa, pxb):
    return np.sqrt(np.sum(np.square(pxa-pxb)))


@nb.njit
def get_filtered_image(img_in, color_to_keep: np.ndarray, color_threshold: np.int64, set_white: bool = True, invert_selection: bool = False):
    """
    Filters the input image for the specified colors, retaining its size, and setting every other color to transparent.

    Parameters
    ----------
    img_in : cv2 image
        The original image set for filtering.
    color_to_keep : 3-length 1d numpy array
        The color you wish to keep in the filtered image.
    color_threshold : float
        How close the color of a given pixel has to be to the one specified in color_to_keep to be kept in.
    set_white : bool
        Whether to set the pixels of the kept color white.
    invert_selection : bool
        Set True to only keep pixels not in colors_to_keep.

    Returns
    -------
    np array
        The filtered RGBA image as a width x height x 4 numpy array.
    """
    img_proc = np.ascontiguousarray(img_in)
    new_img = np.zeros(shape=(img_in.shape[0], img_in.shape[1], 4)).astype(np.uint8)
    for x in range(0, img_proc.shape[0]):
        for y in range(0, img_proc.shape[1]):
            pixel_valid = pixel_color_distance(img_proc[x, y], color_to_keep) < color_threshold
            if (pixel_valid and not invert_selection) or (not pixel_valid and invert_selection):
                new_img[x, y] = np.array([255, 255, 255, 255]).astype(np.uint8) if set_white else np.append(img_proc[x, y], 255).astype(np.uint8)
    return new_img


if __name__ == "__main__":
    start_time = time.perf_counter()
    
    # Prettify area image names
    ims = glob.glob(images_path)
    if len(remove_from_filename) > 0:
        for expression in remove_from_filename:
            for im_path in ims:
                os.rename(im_path, im_path.replace(expression, ""))
            ims = glob.glob(images_path)
            
    if not os.path.exists(f"{save_to}/{area_type}"):
        os.makedirs(f"{save_to}/{area_type}")

    # Get whiteouts of each area
    for img in tqdm(ims):
        imname = img.split("/")[-1]
        img = cv2.cvtColor(cv2.imread(img, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        filtered_img = get_filtered_image(img, area_color, area_threshold, set_white=True)
        cv2.imwrite(f"{save_to}/{area_type}/{imname}", filtered_img)
        
    # Get background for superregion
    img = cv2.cvtColor(cv2.imread(ims[0], cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    filtered_img = get_filtered_image(img, bg_filtered_color, bg_threshold, set_white=False, invert_selection=True)
    filtered_img = get_filtered_image(filtered_image, area_color, bg_threshold, set_white=False, invert_selection=True)
    cv2.imwrite(f"{save_to}/Background.png", cv2.cvtColor(filtered_img, cv2.COLOR_BGR2RGB))
    
    # Generate JSON
    areas = []
    ims = glob.glob(f"{save_to}/{area_type}/*.png")
    for i in enumerate(ims, 1):
        areas.append(
            {
                "Ordinate": i[0], 
                "LatinName": i[1].split("/")[-1][:-4].replace("_", " "), 
                "NativeName": i[1].split("/")[-1][:-4].replace("_", " "), 
                "PhoneticName": "", 
                "SpriteLocation": "/".join(i[1].split("/")[-3:])[:-4]
            })
    
    with open(f"{save_to}/{area_type}.json", 'w+', encoding='utf-8') as f:
        json.dump(areas, f, ensure_ascii=False, indent=4)
    
    print(f"\nBlankmap with {len(ims)} areas created in {round(time.perf_counter() - start_time, 2)} seconds.")
