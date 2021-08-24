"""implement api to access google vision API
"""
import logging
import json
from pathlib import PosixPath, Path
from typing import Union, Optional, List

from google.cloud import vision as gv
from google.cloud.vision_v1 import types, ImageAnnotatorClient

from pysuite.utilities import MAX_RETRY_ATTRIBUTE, SLEEP_ATTRIBUTE


class Vision:
    """Class to interact with Google Vision API

    :param service: an authorized Google Vision service client.
    :param max_retry: max number of retry on quota exceeded error. if 0 or less, no retry will be attempted.
    :param sleep: base number of seconds between retries. the sleep time is exponentially increased after each retry.
    """

    def __init__(self, service: ImageAnnotatorClient, max_retry: int=0, sleep: int=5):
        self._service = service
        setattr(self, MAX_RETRY_ATTRIBUTE, max_retry)
        setattr(self, SLEEP_ATTRIBUTE, sleep)

    @staticmethod
    def load_image(image_path: Union[str, PosixPath]):
        with open(image_path, "rb") as f:
            image = gv.Image(content=f.read())
            return image

    def annotate_image(self, image_path: Union[str, PosixPath], method: str):
        image = Vision.load_image(image_path)
        feature = Vision.translate_method(method)
        request = {
            "image": image,
            "features": [{"type_": feature}]
        }
        response = self._service.annotate_image(request)
        annotated = json.loads(types.image_annotator.AnnotateImageResponse.to_json(response))
        return annotated

    @staticmethod
    def translate_method(method: str):
        try:
            return getattr(types.Feature.Type, method.upper())
        except AttributeError as e:
            logging.critical(f"Cannot find requested method {method}.")
            raise e


