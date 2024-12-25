import curses
import time
import math
import numpy as np
import cv2  # Import cv2 here
from ffpyplayer.player import MediaPlayer

class VideoToCursesASCII_FFplayer:
    def __init__(self, video_path, width=90, height=45, green_thresh=70, alpha=1.2, beta=20):
        self.video_path = video_path
        self.width = width
        self.height = height
        self.green_base = (0, 255, 0)
        self.green_dist = green_thresh
        self.pattern = "OIA"
        self.alpha = alpha
        self.beta = beta
        self.player = None

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        stdscr.clear()

        if not curses.has_colors():
            stdscr.addstr(0, 0, "La terminal no soporta colores.")
            stdscr.refresh()
            time.sleep(2)
            return

        curses.start_color()
        curses.use_default_colors()
        for i in range(256):
            try:
                curses.init_pair(i + 1, i, -1)
            except:
                pass

        self.player = MediaPlayer(self.video_path, ff_opts={'out_fmt': 'rgb24', 'sync': 'audio', 'paused': False})

        while True:
            frame, val = self.player.get_frame()
            if frame is None:
                if val == 'eof':
                    break
                time.sleep(0.01)
                continue

            img, pts = frame
            rgb_buffer = img.to_bytearray()[0]
            w, h = img.get_size()

            arr_rgb = np.frombuffer(rgb_buffer, dtype=np.uint8).reshape((h, w, 3))
            arr_rgb = cv2.resize(arr_rgb, (self.width, self.height))
            arr_rgb = arr_rgb.astype(np.float32)
            arr_rgb = arr_rgb * self.alpha + self.beta
            arr_rgb = np.clip(arr_rgb, 0, 255).astype(np.uint8)
            self._draw_frame(stdscr, arr_rgb)

            if val != 'eof' and val > 0:
                time.sleep(val)

            key = stdscr.getch()
            if key == ord('q'):
                break

        self.player.close_player()

    def _draw_frame(self, stdscr, frame_np):
        height, width, _ = frame_np.shape
        pat_len = len(self.pattern)
        for y in range(height):
            for x in range(width):
                r = int(frame_np[y, x, 0])
                g = int(frame_np[y, x, 1])
                b = int(frame_np[y, x, 2])

                if self._is_greenish(r, g, b):
                    try:
                        stdscr.addstr(y, x, " ", curses.color_pair(0))
                    except:
                        pass
                    continue

                ascii_char = self.pattern[x % pat_len]
                color_idx = self._color_index_256(r, g, b)
                color_pair = curses.color_pair(color_idx + 1)
                try:
                  stdscr.addstr(y, x, ascii_char, color_pair)
                except:
                  pass
        stdscr.refresh()


    def _is_greenish(self, r, g, b):
        dr = r - self.green_base[0]
        dg = g - self.green_base[1]
        db = b - self.green_base[2]
        dist = math.sqrt(dr * dr + dg * dg + db * db)
        return dist < self.green_dist

    def _color_index_256(self, r, g, b):
        R_ = int(r / 256 * 6)
        R_ = min(R_, 5)
        G_ = int(g / 256 * 6)
        G_ = min(G_, 5)
        B_ = int(b / 256 * 6)
        B_ = min(B_, 5)
        return 16 + (36 * R_) + (6 * G_) + B_

def main(stdscr):
    video_path = "video_2024-12-23_19-30-43_3.mp4"  # Replace with your video file path
    video_ascii = VideoToCursesASCII_FFplayer(video_path=video_path, width=90, height=45, green_thresh=100, alpha=1.8, beta=5)
    video_ascii.run(stdscr)

if __name__ == "__main__":
    curses.wrapper(main)
    
    