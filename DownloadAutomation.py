import os
import time
import shutil
import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, radius=15, bg="#4285F4", fg="white", hover_bg="#2a75f3", **kwargs):
        super().__init__(parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.radius = radius
        self.bg = bg
        self.fg = fg
        self.hover_bg = hover_bg
        self.command = command
        self.text = text
        
        self.state = "normal"
        
        self.width = kwargs.get('width', 120)
        self.height = kwargs.get('height', 35)
        self.configure(width=self.width, height=self.height)
        
        self.draw_button()
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
    
    def draw_button(self):
        self.delete("all")
        
        button_bg = self.bg
        if self.state == "hover":
            button_bg = self.hover_bg
        elif self.state == "disabled":
            button_bg = "#cccccc"
        
        # Draw rounded rectangle
        self.create_rounded_rect(0, 0, self.width, self.height, self.radius, fill=button_bg)
        
        # Draw text
        text_color = self.fg if self.state != "disabled" else "#888888"
        self.create_text(self.width//2, self.height//2, text=self.text, fill=text_color, font=("Arial", 11, "bold"))
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_enter(self, event):
        if self.state != "disabled":
            self.state = "hover"
            self.draw_button()
    
    def on_leave(self, event):
        if self.state != "disabled":
            self.state = "normal"
            self.draw_button()
    
    def on_click(self, event):
        if self.state != "disabled":
            self.state = "active"
            self.configure(width=self.width-2, height=self.height-2)
            self.draw_button()
    
    def on_release(self, event):
        if self.state != "disabled":
            self.state = "hover"
            self.configure(width=self.width, height=self.height)
            self.draw_button()
            if self.command:
                self.command()
    
    def config(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
            self.draw_button()
            kwargs.pop("state")
        if "command" in kwargs:
            self.command = kwargs["command"]
            kwargs.pop("command")
        super().config(**kwargs)

class CustomTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, justify="left",
                        background="#ffffcc", relief="solid", borderwidth=1,
                        font=("Arial", "10", "normal"), padx=5, pady=2)
        label.pack(ipadx=3)
    
    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class AnimatedLabel(tk.Label):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.current_alpha = 0
        self.fade_in_progress = False
        self._after_id = None
    
    def fade_in(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self.fade_in_progress = True
        self._fade_step(0, 1)
    
    def fade_out(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self.fade_in_progress = False
        self._fade_step(1, 0)
    
    def _fade_step(self, start, end):
        if self.fade_in_progress and start < end or not self.fade_in_progress and start > end:
            self.current_alpha += 0.1 if self.fade_in_progress else -0.1
            
            if self.current_alpha >= 1 and self.fade_in_progress:
                self.current_alpha = 1
            elif self.current_alpha <= 0 and not self.fade_in_progress:
                self.current_alpha = 0
            
            fg_parts = [int(int(self.cget("fg").replace("#", ""), 16) >> (8*i) & 255) for i in range(2,-1,-1)]
            new_fg = f"#{fg_parts[0]:02x}{fg_parts[1]:02x}{fg_parts[2]:02x}"
            
            self.configure(fg=new_fg)
            
            if (self.fade_in_progress and self.current_alpha < 1) or (not self.fade_in_progress and self.current_alpha > 0):
                self._after_id = self.after(20, lambda: self._fade_step(start, end))

class DownloadSorter:
    def __init__(self):
        self.running = False
        self.observer = None
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Download Sorter")
        self.root.geometry("450x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f7")
        
        # Custom title bar
        title_frame = tk.Frame(self.root, bg="#4285F4", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="Download Sorter", font=("Arial", 16, "bold"), 
                              fg="white", bg="#4285F4")
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Main content frame with shadow effect
        content_frame = tk.Frame(self.root, bg="white", padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # Add a decorative border
        for i in range(4):
            content_frame.grid_columnconfigure(i, weight=1)
            content_frame.grid_rowconfigure(i, weight=1)
        
        border_frame = tk.Frame(content_frame, bg="#e6e6e6", bd=1, relief="solid")
        border_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        inner_frame = tk.Frame(border_frame, bg="white", padx=15, pady=15)
        inner_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # Description
        description = tk.Label(inner_frame, text="This app automatically sorts your downloads\ninto appropriate folders based on file type.", 
                              font=("Arial", 12), bg="white", fg="#555555")
        description.pack(pady=(0, 15))
        
        # Downloads folder selection
        folder_frame = tk.Frame(inner_frame, bg="white")
        folder_frame.pack(fill=tk.X, pady=10)
        
        folder_label = tk.Label(folder_frame, text="Downloads folder:", font=("Arial", 11), 
                               bg="white", fg="#333333")
        folder_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.folder_path = tk.StringVar(value=str(Path.home() / "Downloads"))
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, width=25, 
                                   font=("Arial", 11), bd=2, relief="groove")
        self.folder_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        browse_btn = tk.Button(folder_frame, text="Browse", font=("Arial", 10),
                              relief="raised", bg="#f0f0f0", padx=5,
                              command=self.browse_folder, cursor="hand2")
        browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Status indicator
        status_frame = tk.Frame(inner_frame, bg="white")
        status_frame.pack(fill=tk.X, pady=15)
        
        status_label = tk.Label(status_frame, text="Status:", font=("Arial", 11, "bold"), 
                              bg="white", fg="#333333")
        status_label.pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Not running")
        self.status_indicator = AnimatedLabel(status_frame, textvariable=self.status_var, 
                                           font=("Arial", 11), bg="white", fg="#cc0000")
        self.status_indicator.pack(side=tk.LEFT, padx=(5, 0))
        
        # File type indicators
        types_frame = tk.Frame(inner_frame, bg="white")
        types_frame.pack(fill=tk.X, pady=10)
        
        file_types = [
            ("Images", "#4285F4"), 
            ("Videos", "#EA4335"), 
            ("Documents", "#34A853"), 
            ("Music", "#FBBC05"),
            ("Others", "#9E9E9E")
        ]
        
        for i, (text, color) in enumerate(file_types):
            indicator = tk.Frame(types_frame, width=12, height=12, bg=color)
            indicator.pack(side=tk.LEFT, padx=(0 if i == 0 else 10, 5))
            label = tk.Label(types_frame, text=text, font=("Arial", 10), bg="white")
            label.pack(side=tk.LEFT)
        
        # Buttons
        buttons_frame = tk.Frame(inner_frame, bg="white")
        buttons_frame.pack(pady=20)
        
        self.start_btn = RoundedButton(buttons_frame, text="Start", bg="#4285F4", 
                                     command=self.start_monitoring, width=100)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 20))
        CustomTooltip(self.start_btn, "Start monitoring downloads folder")
        
        self.stop_btn = RoundedButton(buttons_frame, text="Stop", bg="#EA4335", 
                                    command=self.stop_monitoring, width=100)
        self.stop_btn.state = "disabled"
        self.stop_btn.draw_button()
        self.stop_btn.pack(side=tk.LEFT)
        CustomTooltip(self.stop_btn, "Stop monitoring downloads folder")
        
        # Footer
        footer = tk.Label(inner_frame, text="Files will be sorted automatically", 
                         font=("Arial", 9), bg="white", fg="#777777")
        footer.pack(side=tk.BOTTOM, pady=(15, 0))
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
    
    def start_monitoring(self):
        if not os.path.exists(self.folder_path.get()):
            self.status_var.set("Invalid path")
            return
            
        self.running = True
        self.start_btn.state = "disabled"
        self.start_btn.draw_button()
        self.stop_btn.state = "normal"
        self.stop_btn.draw_button()
        self.folder_entry.config(state=tk.DISABLED)
        
        self.status_var.set("Running")
        self.status_indicator.configure(fg="#34A853")
        self.status_indicator.fade_in()
        
        self.show_notification("Download Sorter Started", 
                           "The application is now monitoring your downloads folder.")
        
        event_handler = DownloadEventHandler(self.folder_path.get(), self.show_notification)
        self.observer = Observer()
        self.observer.schedule(event_handler, self.folder_path.get(), recursive=False)
        self.observer.start()
    
    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        self.running = False
        self.start_btn.state = "normal"
        self.start_btn.draw_button()
        self.stop_btn.state = "disabled"
        self.stop_btn.draw_button()
        self.folder_entry.config(state=tk.NORMAL)
        
        self.status_var.set("Stopped")
        self.status_indicator.configure(fg="#cc0000")
        
        self.show_notification("Download Sorter Stopped", 
                           "The application has stopped monitoring your downloads folder.")
    
    def show_notification(self, title, message):
        notification = tk.Toplevel(self.root)
        notification.title("")
        notification.geometry("300x100+{}+{}".format(
            self.root.winfo_x() + self.root.winfo_width(),
            self.root.winfo_y() + 50
        ))
        notification.configure(bg="white")
        notification.overrideredirect(True)
        notification.attributes("-topmost", True)
        
        # Add a border
        border_frame = tk.Frame(notification, bg="#4285F4", bd=2)
        border_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        inner_frame = tk.Frame(border_frame, bg="white")
        inner_frame.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
        
        # Title
        title_label = tk.Label(inner_frame, text=title, font=("Arial", 12, "bold"), 
                              bg="white", fg="#333333")
        title_label.pack(padx=10, pady=(10, 5), anchor="w")
        
        # Message
        message_label = tk.Label(inner_frame, text=message, font=("Arial", 10), 
                               bg="white", fg="#555555", wraplength=280, justify="left")
        message_label.pack(padx=10, pady=(0, 10), anchor="w")
        
        # Auto-hide after 3 seconds
        notification.after(3000, notification.destroy)
    
    def on_close(self):
        if self.running:
            self.stop_monitoring()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self, download_folder, notification_callback=None):
        self.download_folder = download_folder
        self.notification_callback = notification_callback
        self.destination_folders = {
            'images': os.path.join(download_folder, 'Images'),
            'videos': os.path.join(download_folder, 'Videos'),
            'documents': os.path.join(download_folder, 'Documents'),
            'music': os.path.join(download_folder, 'Music'),
            'applications': os.path.join(download_folder, 'Applications'),
            'archives': os.path.join(download_folder, 'Archives')
        }
        
        for folder in self.destination_folders.values():
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def on_created(self, event):
        if event.is_directory:
            return
            
        self.process_file(event.src_path)
    
    def on_moved(self, event):
        if event.is_directory:
            return
            
        if self.download_folder in event.dest_path:
            self.process_file(event.dest_path)
    
    def process_file(self, file_path):
        if not os.path.exists(file_path):
            return
            
        time.sleep(1)  # Wait for file to be completely downloaded
        
        file_type = self.get_file_type(file_path)
        if file_type in self.destination_folders:
            destination = self.destination_folders[file_type]
            filename = os.path.basename(file_path)
            dest_path = os.path.join(destination, filename)
            
            try:
                shutil.move(file_path, dest_path)
                if self.notification_callback:
                    self.notification_callback(
                        "File Sorted",
                        f"'{filename}' moved to {file_type.capitalize()} folder"
                    )
            except Exception:
                pass
                
    def get_file_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm']
        document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.rtf', '.odt']
        music_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        application_extensions = ['.exe', '.msi', '.app', '.dmg', '.deb', '.rpm']
        archive_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
        
        if ext in image_extensions:
            return 'images'
        elif ext in video_extensions:
            return 'videos'
        elif ext in document_extensions:
            return 'documents'
        elif ext in music_extensions:
            return 'music'
        elif ext in application_extensions:
            return 'applications'
        elif ext in archive_extensions:
            return 'archives'
        else:
            return None

if __name__ == "__main__":
    app = DownloadSorter()
    app.run()