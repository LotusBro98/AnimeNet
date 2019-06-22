import http.server
import io

import segmenter.segmenter as seg
import drawer.drawer as drw

import numpy as np
import png

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


class DoodleHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(bytes("<html><body><h1>hi!</h1></body></html>", encoding='utf-8'))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        # Doesn't do anything with posted data
        print(self.path)
        if self.path == "/draw":
            head = decode_png(self.rfile.read(int(self.headers['size_head'])))
            eyes = decode_png(self.rfile.read(int(self.headers['size_eyes'])))
            hair = decode_png(self.rfile.read(int(self.headers['size_hair'])))

            anime = drw.draw(drawer, head, eyes, hair)

            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()

            self.wfile.write(encode_png(anime))
        elif self.path == "/segmentize":
            photo = decode_png(self.rfile.read(int(self.headers['size'])))

            head, eyes, hair = seg.segmentize(segmenter, photo)

            head = encode_png(head)
            eyes = encode_png(eyes)
            hair = encode_png(hair)

            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.send_header('size_head', str(len(head)))
            self.send_header('size_eyes', str(len(eyes)))
            self.send_header('size_hair', str(len(hair)))
            self.end_headers()

            self.wfile.write(head + eyes + hair)
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            self.wfile.write(bytes("Wrong command", encoding='utf-8'))

def run_server(port=80):
    global drawer
    drawer = drw.restore_generator()

    global segmenter
    segmenter = seg.restore_segmenter()


    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, DoodleHandler)
    httpd.serve_forever()


if __name__ == '__main__':
    run_server()