"""Implement api to access google vision API
"""
import logging
import json
from pathlib import PosixPath
from typing import Union, Optional, List

from google.cloud import vision as gv
from google.cloud.vision_v1.types import AnnotateImageResponse
from google.cloud.vision_v1.types.image_annotator import BatchAnnotateImagesResponse
from google.cloud.vision_v1 import types, ImageAnnotatorClient


class Vision:
    """Class to interact with Google Vision API.

    :param service: an authorized Google Vision service client.
    """

    def __init__(self, service: ImageAnnotatorClient):
        self._service = service
        self._requests = []

    @staticmethod
    def load_image(image_path: Union[str, PosixPath]) -> gv.Image:
        """Load a local image as Image class that can be used to submit image annotation requests.

        :param image_path: Path to the image file.
        :return: Loaded Image object from the target file
        """
        with open(image_path, "rb") as f:
            image = gv.Image(content=f.read())
            return image

    def add_request(self, image_path: Union[str, PosixPath], methods: Union[List[str], str]):
        """Add a request to annotate a local image. Multiple annotation methods can be added at the same time. The
        request will not be immediately submitted. This method is only useful for `batch_annotate_image`.

        :example:

        >>> vision.add_request("/my/image.png", methods=["LABEL_DETECTION", "test_detection"])

        :param image_path: Path to the image file.
        :param methods: A list of strings representing supported annotation methods. Please view
          google.cloud.vision_v1.types.Feature.Type for all supported methods. They are case-insensitive.
        :return: None
        """
        request = self._create_request(image_path, methods)
        self._requests.append(request)

    def annotate_image(
            self, image_path: Union[str, PosixPath], methods: Union[List[str], str]
    ) -> AnnotateImageResponse:
        """Submit a request to annotate a local image using specified methods.

        :param image_path: Path to the image file.
        :param methods: A list of strings representing supported annotation methods. Please view
          google.cloud.vision_v1.types.Feature.Type for all supported methods. They are case-insensitive.
        :return: An AnnotateImageResponse object with annotated content.
        """
        request = self._create_request(image_path, methods)

        response = self._service.annotate_image(request=request)
        return response

    def batch_annotate_image(self) -> Optional[BatchAnnotateImagesResponse]:
        """Submit the prepared requests to annotate images and return a response with annotated content. You must first
        call `add_request` to prepare the configurations. If no configurations were prepared, this method will return
        None.

        :return: An BatchAnnotateImagesResponse object with annotated content. Or None if no requests were prepared.
        """
        if not self._requests:
            logging.warning("No requests was prepared")
            return

        response = self._service.batch_annotate_images(requests=self._requests)
        return response

    def async_annotate_image(self):
        raise NotImplementedError("This method has not been implemented.")

        if not self._requests:
            logging.warning("No requests was prepared")
            return

        response = self._service.async_batch_annotate_images(requests=self._requests, output_config=dict())
        return response

    @staticmethod
    def _translate_method(method: str):
        """Translate string method to corresponding feature type in google.cloud.vision_v1.types.Feature.Type. This is
        case insensitive. If no such type is implemented, a NotImplementedError will be raised.

        :param method: A string representation of feature type implemented in google vision.
        :return: The corresponding attributes of feature type.
        """
        try:
            return getattr(types.Feature.Type, method.upper())
        except AttributeError as e:
            raise NotImplementedError(f"Cannot find requested method {method}.") from e

    @staticmethod
    def _create_request(image_path: Union[str, PosixPath], methods: Union[List[str], str]) -> dict:
        if isinstance(methods, str):
            methods = [methods]
        features = []
        for method in methods:
            features.append({"type_": Vision._translate_method(method)})

        image = Vision.load_image(image_path)
        request = {
            "image": image,
            "features": features
        }
        return request

    @staticmethod
    def to_json(response: Union[AnnotateImageResponse, BatchAnnotateImagesResponse]) -> dict:
        """Convert possible image responses to dictionary. If it's not a supported response, a type error will be
        raised.

        :param response: A response returned from `annotate_image` or `batch_annotate_image`.
        :return: A dictionary containing annotated contents.
        """
        if isinstance(response, AnnotateImageResponse):
            annotated = json.loads(types.image_annotator.AnnotateImageResponse.to_json(response))
        elif isinstance(response, BatchAnnotateImagesResponse):
            annotated = json.loads(types.image_annotator.BatchAnnotateImagesResponse.to_json(response))
        else:
            raise TypeError(f"Invalid type of response. Expecting AnnotateImageResponse or BatchAnnotateImagesResponse."
                            f"Got {type(response)}")

        return annotated
