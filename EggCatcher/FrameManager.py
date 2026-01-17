from AdbFastScreenshots import AdbFastScreenshots
import time


class FrameManager:


    def __init__(self, orig_screen_size, target_screen_size):

        self.orig_w, self.orig_h = orig_screen_size

        self.frame_w, self.frame_h = target_screen_size

    def map_point_to_original(self, pt):
        """Mappa un punto (x,y) dalle coordinate del frame corrente alla risoluzione originale.
        Usa LAST_ORIG_SIZE impostato in get_frame(). Restituisce (x_orig, y_orig) interi.
        """
        
        # Calcolo scale separati nel caso non sia proporzionale
        scale_x = self.orig_w / float(self.frame_w)
        scale_y = self.orig_h / float(self.frame_h)

        return (int(pt[0] * scale_x), int(pt[1] * scale_y))

    def map_x_to_original(self, x):
        scale_x = self.orig_w / float(self.frame_w)
        

        return int(x * scale_x)

    def map_size_to_original(self, w_h):
        """Mappa una dimensione (w,h) del frame corrente alla risoluzione originale."""

        scale_x = self.orig_w / float(self.frame_w)
        scale_y = self.orig_h / float(self.frame_h)
        return (int(w_h[0] * scale_x), int(w_h[1] * scale_y))