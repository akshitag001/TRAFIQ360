import os
from PIL import Image

# Setup paths
brain_dir = r"C:\Users\Akshit aggarwal\.gemini\antigravity-ide\brain\ecc1739f-3df3-4ee0-9068-c356b4b61b90"
workspace_dir = r"c:\Users\Akshit aggarwal\Downloads\TRAFIQ360"
static_dir = os.path.join(workspace_dir, "static", "avatars")

os.makedirs(static_dir, exist_ok=True)

sheet_path = os.path.join(brain_dir, "media__1781583384316.jpg")
img = Image.open(sheet_path)

# Let's crop:
# 1. 3D Avatars (Row 3, bottom-left)
# y range is approx 580 to 670
# X centers are approx 65, 155, 245, 335, 425 with radius 40
crops = {
    "avatar_grey.png": (25, 580, 105, 660),
    "avatar_blue.png": (115, 580, 195, 660),
    "avatar_green.png": (205, 580, 285, 660),
    "avatar_yellow.png": (295, 580, 375, 660),
    "avatar_purple.png": (385, 580, 465, 660),
    
    # 2. Large Standing Officer (Left)
    "pose_standing.png": (10, 40, 185, 540),
    
    # 3. Action Poses (Row 2, mid-left, y range 310 to 530)
    "pose_radio.png": (210, 510, 290, 680),  # Wait, let's verify if Action Poses are in row 2 or row 3. 
    # Let's save both crop attempts to see which one contains the actual poses!
    "pose_radio_row2.png": (210, 310, 290, 480),
    "pose_stop_row2.png": (310, 310, 390, 480),
    "pose_pointing_row2.png": (410, 310, 490, 480),
    "pose_writing_row2.png": (510, 310, 590, 480),

    "pose_radio_row3.png": (210, 510, 290, 680),
    "pose_stop_row3.png": (310, 510, 390, 680),
    "pose_pointing_row3.png": (410, 510, 490, 680),
    "pose_writing_row3.png": (510, 510, 590, 680),
}

for filename, box in crops.items():
    try:
        cropped = img.crop(box)
        cropped.save(os.path.join(static_dir, filename))
        print(f"Saved {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {e}")
