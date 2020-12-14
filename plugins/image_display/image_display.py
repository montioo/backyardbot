#
# image_display.py
# backyardbot
#
# Created: December 2020
# Author: Marius Montebaur
# montebaur.tech, github.com/montioo
#

from framework.plugin import Plugin
import base64
import os


class ImageDisplay(Plugin):
    """
    Plugin will load an image and display it in the frontend. It is not
    dependent on the server loading the image (or allowing the image to be
    loaded) because the image is base64 encoded and included in the template
    rendering.
    """

    def initialize(self, settings):
        """ Loading the image and saving it as a b64 encoded string. """
        image_path = settings["image_path"]
        self.image_extension = os.path.splitext(image_path)[1][1:]
        if not self.image_extension:
            self.logger.warning(f"Couldn't get image file extension for image at path {image_path}")

        self.logger.info(f"Will load image with extension {self.image_extension} from {image_path}")

        # TODO: Which origin is used for relative paths?
        with open(image_path, "rb") as f:
            self.image_data = base64.b64encode(f.read()).decode()

    def calc_render_data(self):
        """ Giving image data and file type to renderer. """
        return {
            "image_data": self.image_data,
            "image_extension": self.image_extension
        }