import os, glob
from PIL import Image

# Creats dark icons

icon_folder = 'icons'
new_folder = 'dark_icons'
if not os.path.exists(new_folder):
    os.mkdir(new_folder)

for icon in glob.glob(icon_folder + '/*.png'):
    im = Image.open(icon)
    icon_name = os.path.split(icon)[-1]
    print(icon_name)
    r, g, b, a = im.split()

    def invert(image):
        return image.point(lambda p: 255 - p)

    r, g, b = map(invert, (r, g, b))
    im_invert = Image.merge(im.mode, (r, g, b, a))
    im_invert.save(new_folder + '/' + icon_name)
