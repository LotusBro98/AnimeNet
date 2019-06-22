import io

import numpy as np
import png

import cv2 as cv
import requests as rq
import os
os.environ['NO_PROXY'] = '127.0.0.1'

def decode_png(png_bytes, size=(256, 256)):
    img = png.Reader(bytes=png_bytes).read()
    img = np.vstack(map(np.uint8, img[2]))
    img = np.reshape(img, size + (4,))
    return img

def encode_png(img):
    w = img.shape[1]
    h = img.shape[0]
    buf = io.BytesIO()
    png.Writer(w, h, alpha=True).write(buf, np.reshape(img, (-1, w * 4)))
    buf.seek(0,0)
    return buf.read()

def request_anime(head, eyes, hair):
    head = encode_png(head)
    eyes = encode_png(eyes)
    hair = encode_png(hair)

    headers = {
        'Content-Type': 'image/png',
        'size_head': str(len(head)),
        'size_eyes': str(len(eyes)),
        'size_hair': str(len(hair)),
    }

    res = rq.post("http://127.0.0.1/draw", headers=headers, data=head + eyes + hair)
    anime = decode_png(res.content)

    return anime

def request_segments(photo):
    photo = encode_png(photo)

    headers = {
        'Content-Type': 'image/png',
        'size': str(len(photo)),
    }

    res = rq.post("http://127.0.0.1/segmentize", headers=headers, data=photo)

    size_head = int(res.headers["size_head"])
    size_eyes = int(res.headers["size_eyes"])
    size_hair = int(res.headers["size_hair"])

    bytes = res.content
    head = bytes[:size_head]
    bytes = bytes[size_head:]
    eyes = bytes[:size_eyes]
    bytes = bytes[size_eyes:]
    hair = bytes[:size_hair]

    head = decode_png(head)
    eyes = decode_png(eyes)
    hair = decode_png(hair)

    return head, eyes, hair


if __name__ == '__main__':
    head = cv.imread("img/head.png", cv.IMREAD_UNCHANGED)
    eyes = cv.imread("img/eyes.png", cv.IMREAD_UNCHANGED)
    hair = cv.imread("img/hair.png", cv.IMREAD_UNCHANGED)

    anime = request_anime(head, eyes, hair)

    head, eyes, hair = request_segments(anime)

    cv.imshow("Anime", cv.cvtColor(anime, cv.COLOR_RGBA2BGRA))
    cv.imshow("Head", cv.cvtColor(head, cv.COLOR_RGBA2BGRA))
    cv.imshow("Eyes", cv.cvtColor(eyes, cv.COLOR_RGBA2BGRA))
    cv.imshow("Hair", cv.cvtColor(hair, cv.COLOR_RGBA2BGRA))
    cv.waitKey()