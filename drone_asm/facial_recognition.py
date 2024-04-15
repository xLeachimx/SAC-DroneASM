# File: facial_recognition.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2023
# License: GNU GPLv3
# Created On: 01 Apr 2024
# Purpose:
# Notes:

# File: face_recog.py
# Author: Michael Huelsman
# Copyright: Dr. Michael Andrew Huelsman 2023
# License: GNU GPLv3
# Created On: 25 Mar 2024
# Purpose:
# Notes:

import os.path
from typing import Sequence

import cv2 as cv
import numpy as np

_file_location = os.path.dirname(os.path.abspath(__file__))

_face_detector = cv.FaceDetectorYN_create(os.path.join(_file_location, "models", "face_detection_yunet_2023mar.onnx"), "", (0, 0))
_face_detector.setScoreThreshold(0.87)
_face_recognizer = cv.FaceRecognizerSF_create(os.path.join(_file_location, "models", "face_recognition_sface_2021dec.onnx"), "")
_COSINE_THRESHOLD = 0.5

def find_faces(img):
    """
    :param img:
        An openCV image (numpy array) in RGB format
    :return:
        Returns a list of face locations.
    """
    result = []
    height, width, _ = img.shape
    _face_detector.setInputSize((width, height))
    try:
        _, faces = _face_detector.detect(img)
        if len(faces) == 0:
            return result
        return faces
    except Exception as _:
        return []

def encode_face(img, face_location):
    """
    Encodes the face in the image at the provided location for later recognition.
    :param img:
        An openCV image (numpy array) in RGB format.
    :param face_location:
        A raw face location including the bounding box and 5-point face landmarks
    :return:
        A 128 dimensional vector representing the face.
    """
    try:
        aligned_face = _face_recognizer.alignCrop(img, face_location)
        return _face_recognizer.feature(aligned_face)
    except Exception as _:
        return None

def detect_face(unknown_encoding: np.ndarray, known_encodings: list[np.ndarray], names: list[str] = ()) -> str | int:
    """
    :param unknown_encoding:
        The 128 dimensional encoding of an unknown face.
    :param known_encodings:
        A list (or other iterable) of known 128 dimensional face encodings.
    :param names:
        A list of names which is parallel to known_encodings.
    :return:
        Returns the matching name to the most similar known encoding.
        If names does not have an entry or otherwise could not access the entry
        returns the index of the most similar encoding.
        If no name exceeds a defined
        similarity threshold then Unknown is returned.
    """
    best_sim = 0.0
    best_match = -1
    for idx, encoding in enumerate(known_encodings):
        sim = _face_recognizer.match(unknown_encoding, encoding, cv.FACE_RECOGNIZER_SF_FR_COSINE)
        if best_match < 0 or sim > best_sim:
            best_match = idx
            best_sim = sim
    if best_sim < _COSINE_THRESHOLD:
        return "Unknown"
    try:
        return names[best_match]
    except IndexError:
        return best_match


def face_similarity(unknown_encoding: np.ndarray, known_encoding: np.ndarray):
    """
    :param unknown_encoding:
        The 128 dimensional encoding of an unknown face.
    :param known_encoding:
        A known 128 dimensional face encoding.
    :return:
        Returns the modified cosine similarity between the two encodings.
        0.0 means absolutely no match.
        1.0 means exact match.
    """
    return _face_recognizer.match(unknown_encoding, known_encoding, cv.FACE_RECOGNIZER_SF_FR_COSINE)

def face_location_to_dict(raw_face_location: Sequence) -> dict:
    """
    Converts the raw face location into an easy to use dictionary.
    :param raw_face_location:
        A sequence of float indicating the locations of a face in its 5-point landmarks.
    :return:
        Returns a dictionary with entries of rect, right_eye, left_eye, nose_tip, right_mouth,
        and left_mouth. The rect entry is given as (top, left, height, width)
    """
    raw_face_location = list(map(int, raw_face_location))
    result = {'rect': raw_face_location[:4],
              'right_eye': (raw_face_location[4], raw_face_location[5]),
              'left_eye': (raw_face_location[6], raw_face_location[7]),
              'nose_tip': (raw_face_location[8], raw_face_location[9]),
              'right_mouth': (raw_face_location[10], raw_face_location[11]),
              'left_mouth': (raw_face_location[12], raw_face_location[13])
              }
    return result