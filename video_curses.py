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
        curses.curs_set(1)  # Use non-permitted colors by default to allow terminal operations
        stdscr.nodelay(True)
        stdscr.clear()

        if not curses.has_colors():
            print("La terminal no soporta colores.")
            stdscr.refresh()
            time.sleep(2)
            return

        curses.start_color()
        curses.use_default_colors()

        try:
            for i in range(256):
                curses.init_pair(i + 1, i, -1)

            self.player = MediaPlayer(
                video_path,
                ff_opts={
                    'out_fmt': 'rgb24',
                    'sync': True,
                    'paused': False
                }
            )

            while True:
                # Read frame from player
                frame, val = self.player.get_frame()
                if frame is None:
                    if val == 'eof':
                        break
                    time.sleep(0.01)
                    continue

                img, pts = frame
                rgb_buffer = img.to_bytearray()[0]
                
                w, h = img.get_size()
                # Resize the image to fit the terminal window while maintaining aspect ratio
                resized_img = cv2.resize(
                    np.frombuffer(rgb_buffer, dtype=np.uint8).reshape((h, w, 3)),
                    (self.width, self.height),
                    interpolation=cv2.INTER_AREA
                )
                
                arr_rgb = resized_img.astype(np.float32)
                arr_rgb = arr_rgb * self.alpha + self.beta
                arr_rgb = np.clip(arr_rgb, 0, 255).astype(np.uint8)
                
                self._draw_frame(stdscr, arr_rgb)

                if val != 'eof' and val > 0:
                    time.sleep(val)

                key = stdscr.getch()
                if key == ord('q'):
                    break

        finally:
            self.player.close_player()

    def _draw_frame(self, stdscr, frame_np):
        height, width, channels = frame_np.shape
        pat_len = len(self.pattern)
        
        try:
            for y in range(height):
                for x in range(width):
                    r = int(frame_np[y, x, 0])
                    g = int(frame_np[y, x, 1])
                    b = int(frame_np[y, x, 2])

                    if self._is_greenish(r, g, b):
                        # Display a space in color pair 0 (black)
                        stdscr.addstr(y, x, " ", curses.color_pair(0))
                        continue

                    # Get the corresponding ASCII character from the pattern
                    ascii_char = self.pattern[x % pat_len]
                    # Determine the color based on pixel brightness
                    color_idx = self._color_index_256(r, g, b)
                    color_pair = curses.color_pair(color_idx + 1)
                    
                    try:
                        stdscr.addstr(y, x, ascii_char, color_pair)
                    except:
                        pass

            stdscr.refresh()

        finally:
            cv2.destROYAllWindows()

    def _is_greenish(self, r, g, b):
        green_base = self.green_base
        dr = r - green_base[0]
        dg = g - green_base[1]
        db = b - green_base[2]
        
        dist_sq = dr * dr + dg * dg + db * db
        return dist_sq < (self.green_dist ** 2)

    def _color_index_256(self, r, g, b):
        R = int(r / 256.0 * 6)
        G = int(g / 256.0 * 6)
        B = int(b / 256.0 * 6)
        
        return min(16 + (36 * R) + (6 * G) + B, 255)

def main(stdscr):
    # Use a try-except block to handle cases where the video_path doesn't exist
    try:
        video_path = "video_2024-12-23_19-30-43_3.mp4"  # Replace with your desired path
        video_ascii = VideoToCursesASCII_FFplayer(
            video_path=video_path,
            width=90,
            height=45,
            green_thresh=70,
            alpha=1.2,
            beta=20
        )
        video_ascii.run(stdscr)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except Exception as e:
        print(f"Terminal error: {str(e)}")
