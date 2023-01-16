import os
import time
import yaml
import argparse
from tkinter import Frame, BOTH, YES, Toplevel, Tk, Canvas
import threading
import gi
gi.require_version('Wnck','3.0')
from gi.repository import Wnck, Gtk

# install dependencies:
# apt-get install vlc vlc-plugin-access-extra
# apt-get install python3-gi gir1.2-wnck-3.0

def wait_for_vlc():
    found_window = False
    while True:
        screen = Wnck.Screen.get_default()
        screen.force_update()
        windows = screen.get_windows()
        del screen
        for window in windows:
            if 'vlc' in window.get_name().lower():
                found_window = True
        Gtk.main_iteration()
        if found_window:
            break
        time.sleep(0.1)


def broadcast_screen(x1, y1, x2, y2):    
    fps = 30
    os.system(
        "vlc --no-video-deco "
        "--no-embedded-video "
        f"--screen-fps={fps} "
        f"--screen-top={int(y1)} "
        f"--screen-left={int(x1)} "
        f"--screen-width={int(x2 - x1)} "
        f"--screen-height={int(y2 - y1)} "
        "screen:// &"
    )
    
    wait_for_vlc()

    screen = Wnck.Screen.get_default()
    screen.force_update()
    windows = screen.get_windows()
    for window in windows:
        if 'vlc' in window.get_name().lower():
            window.make_below()


def load_preset(path):
    if os.path.isfile(path):
        with open(path) as file:
            config = yaml.safe_load(file.read())
        if config is None:
            config = {}
        return config
    else:
        return {}


def save_preset(path, name, x1, y1, x2, y2):
    config = load_preset(path)
    config[name] = (x1, y1, x2, y2)    
    with open(path, 'w') as file:
        yaml.safe_dump(config, file)
    

class Application():
    def __init__(self, master, preset_name: str, config_path: str):
        self.snip_surface = None
        self.master = master
        self.start_x = 0.0
        self.start_y = 0.0
        self.current_x = 0.0
        self.current_y = 0.0
        self.config_path = config_path
        self.preset_name = preset_name
        
        root.geometry('50x50+200+200')  # set new geometry
        root.title('Broadcast Screen')

        self.menu_frame = Frame(master, width=50, height=50, background="gray")
        self.menu_frame.pack(fill=BOTH, expand=YES, padx=1, pady=1)

        self.master_screen = Toplevel(root)
        root.deiconify()
        root.withdraw()
        self.picture_frame = Frame(self.master_screen, background="maroon3")
        self.picture_frame.pack(fill=BOTH, expand=YES)
        
        self.run_capture_thread = threading.Thread(target=self.run_capture)
        self.run_capture_thread.daemon = True
        self.run_capture_thread.start()

    def run_capture(self):
        time.sleep(0.25)
        self.create_screen_canvas()

    def create_screen_canvas(self):
        print("Capture screen")
        self.master_screen.deiconify()
        root.withdraw()

        self.snip_surface = Canvas(self.picture_frame, cursor="cross", bg="grey11")
        self.snip_surface.pack(fill=BOTH, expand=YES)

        self.snip_surface.bind("<ButtonPress-1>", self.on_button_press)
        self.snip_surface.bind("<B1-Motion>", self.on_snip_drag)
        self.snip_surface.bind("<ButtonRelease-1>", self.on_button_release)

        self.master_screen.attributes('-fullscreen', True)
        self.master_screen.attributes('-alpha', 0.2)
        self.master_screen.lift()
        self.master_screen.attributes("-topmost", True)

    def on_button_release(self, event):
        try:
            x1 = int(min(self.start_x, self.current_x))
            x2 = int(max(self.start_x, self.current_x))
            y1 = int(min(self.start_y, self.current_y))
            y2 = int(max(self.start_y, self.current_y))

            broadcast_screen(x1, y1, x2, y2)
            if len(self.config_path) != 0 and len(self.preset_name) != 0:
                save_preset(self.config_path, self.preset_name, x1, y1, x2, y2)
        finally:
            self.exit_screenshot_mode()
        return event

    def exit_screenshot_mode(self):
        self.snip_surface.destroy()
        self.master_screen.withdraw()
        root.deiconify()
        root.quit()

    def on_button_press(self, event):
        # save mouse drag start position
        self.start_x = self.snip_surface.canvasx(event.x)
        self.start_y = self.snip_surface.canvasy(event.y)
        self.snip_surface.create_rectangle(0, 0, 1, 1, outline='red', width=3, fill="maroon3")

    def on_snip_drag(self, event):
        self.current_x, self.current_y = (event.x, event.y)
        # expand rectangle as you drag the mouse
        self.snip_surface.coords(1, self.start_x, self.start_y, self.current_x, self.current_y)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="broadcast_screen")
  
    parser.add_argument(
        "-p",
        "--preset",
        type=str,
        default="",
        help="screen preset config",
    )
    
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="./config.yaml",
        help="preset config path",
    )
    args = parser.parse_args()
    
    config = load_preset(args.config)
    
    if len(args.preset) == 0 or args.preset not in config:
        root = Tk()
        app = Application(root, args.preset, args.config)
        root.mainloop()
    else:
        x1, y1, x2, y2 = config[args.preset]
        broadcast_screen(x1, y1, x2, y2)
