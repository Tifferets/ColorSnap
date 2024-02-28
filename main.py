from datetime import datetime
from PIL import Image as PILImage
from PIL import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage  # Rename to avoid conflicts
from kivymd.uix.label import MDLabel
from tkinter import Tk, filedialog
import cv2
import pandas as pd
from kivy.uix.camera import Camera
from kivymd.app import MDApp
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.screen import Screen
import colorsys
from kivy.uix.popup import Popup
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
import matplotlib

matplotlib.use('Agg')  # Use Agg backend for matplotlib

# Define a custom widget for displaying color rectangles
class ColorRectangle(Widget):
    color = ListProperty([1, 1, 1, 1])  # Initialize color property

    def __init__(self, color, **kwargs):
        super(ColorRectangle, self).__init__(**kwargs)
        self.color = color  # Set initial color

        # Draw a rectangle with the specified color
        with self.canvas:
            Color(rgba=self.color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

    def on_color(self, instance, value):
        # Update the color when the color property changes
        if hasattr(self, 'rect'):
            self.rect.color = value

    def on_size(self, *args):
        if hasattr(self, 'rect'):
            self.rect.size = self.size

    def on_pos(self, *args):
        if hasattr(self, 'rect'):
            self.rect.pos = self.pos

# Define the main application class
class ColorDetectionApp(MDApp):
    def __init__(self, **kwargs):
        super(ColorDetectionApp, self).__init__(**kwargs)
        self.camera = None
        self.generate_matching_colors_button = None
        self.color_info_label = None
        self.open_camera_button = None
        self.upload_Image = None
        self.screen = None
        self.selected_image_path = None
        self.img = None
        self.camera_button_text = "Open Camera"
        self.is_camera_open = False
        self.image_widget = KivyImage(allow_stretch=False, keep_ratio=True, size_hint=(0.7, 0.7),
                                      pos_hint={'center_x': 0.5, 'center_y': 0.6})  # Use KivyImage
        self.layout = None
        self.csv = None
        self.rect = None
        self.hex_value = None

    def build(self):
        # Create the main screen
        self.screen = Screen()

        # Create buttons and labels
        self.open_camera_button = MDRectangleFlatButton(text=self.camera_button_text, size_hint=(0.25, 0.1),
                                                        pos_hint={'center_x': 0.2, 'center_y': 0.1})
        self.open_camera_button.bind(on_press=self.toggle_camera)

        self.upload_Image = MDRectangleFlatButton(text='Upload Image', size_hint=(0.25, 0.1),
                                                  pos_hint={'center_x': 0.8, 'center_y': 0.1})
        self.upload_Image.bind(on_press=self.open_file_explorer)

        self.generate_matching_colors_button = MDRectangleFlatButton(text='Generate Matching Colors',
                                                                     size_hint=(0.25, 0.1),
                                                                     pos_hint={'center_x': 0.5, 'center_y': 0.1})
        self.generate_matching_colors_button.bind(on_press=self.on_generate_matching_colors)

        self.color_info_label = MDLabel(text='', size_hint=(None, None), size=(2000, 50), width=500, halign="center",
                                        pos_hint={'center_x': 0.5, 'center_y': 0.2},
                                        text_size=(None, None))

        # Add widgets to the screen
        self.screen.add_widget(self.color_info_label)
        self.screen.add_widget(self.open_camera_button)
        self.screen.add_widget(self.upload_Image)
        return self.screen

    def toggle_camera(self, instance):
        # Toggle the camera state (open/close)
        if self.color_info_label in self.screen.children:
                self.screen.remove_widget(self.color_info_label)

        if not self.is_camera_open:
            # Open camera
            self.camera = Camera(play=True, resolution=(640, 720))
            self.camera.keep_ratio = True

            if self.layout:
                self.layout.clear_widgets()

            self.layout = BoxLayout(orientation='horizontal')
            self.layout.add_widget(self.camera)

            self.camera.size_hint = (0.9, 0.9)
            self.camera.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

            screen = self.root
            screen.add_widget(self.layout)

            self.open_camera_button.text = "Take Picture"
            self.is_camera_open = True
        else:
            # Capture image and close camera
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            image_filename = f"captured_image_{timestamp}.png"

            image_data = self.camera.export_as_image()
            image_data.save(image_filename)

            self.selected_image_path = image_filename
            self.display_image()

            self.open_camera_button.text = "Open Camera"
            self.is_camera_open = False

            self.layout.remove_widget(self.camera)

    def open_file_explorer(self, instance):
        # Open file explorer to select an image file
        if self.color_info_label in self.screen.children:
            self.screen.remove_widget(self.color_info_label)
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename()
        root.destroy()

        if file_path:
            self.selected_image_path = file_path
            self.display_image()

    def display_image(self):
        # Display the selected image on the screen
        if self.selected_image_path:
            if not self.layout:
                self.layout = BoxLayout(orientation='horizontal')

            if not self.image_widget:
                self.image_widget = KivyImage(allow_stretch=False, keep_ratio=True)

            self.image_widget.source = self.selected_image_path
            self.image_widget.size_hint = (0.8, 0.7)
            self.image_widget.pos_hint = {'center_x': 0.5, 'center_y': 0.6}

            self.layout.clear_widgets()
            self.layout.add_widget(self.image_widget)

            if not self.layout.parent:
                screen = self.root
                screen.add_widget(self.layout)

            self.img = cv2.imread(self.selected_image_path)
            self.detect_colors()
            self.image_widget.bind(on_touch_down=self.on_touch_down)

            # Add the "Generate Matching Colors" button only if it's not already present
            if self.generate_matching_colors_button not in self.screen.children:
                self.screen.add_widget(self.generate_matching_colors_button)

            if self.color_info_label not in self.screen.children:
                self.color_info_label.text = ''
                if self.rect:
                    self.color_info_label.canvas.before.remove(self.rect)
                self.screen.add_widget(self.color_info_label)
        else:
            # Remove the "Generate Matching Colors" button if no image is displayed
            if self.generate_matching_colors_button in self.screen.children:
                self.screen.remove_widget(self.generate_matching_colors_button)

    def detect_colors(self):
        # Load color names from CSV file for color detection
        if self.img is not None:
            index = ["color_name", "hexa", "R", "G", "B"]
            self.csv = pd.read_csv('color_names_1200.csv', names=index, header=None)

    def on_touch_down(self, widget, touch):
        # Handle touch events on the image widget
        if self.image_widget.collide_point(*touch.pos):
            print(touch)
            touch_x = (touch.pos[0] - self.image_widget.x) * (
                    self.image_widget.texture_size[0] / self.image_widget.width)
            touch_y = (touch.pos[1] - self.image_widget.y) * (
                    self.image_widget.texture_size[1] / self.image_widget.height)
            print(touch_x)
            print(touch_y)
            touch_x = max(0, min(self.image_widget.texture_size[0] - 1, touch_x))
            touch_y = max(0, min(self.image_widget.texture_size[1] - 1, touch_y))

            b, g, r = self.img[int(touch_y), int(touch_x)]
            print(b+ g+ r)
            b = max(0, min(255, b))
            g = max(0, min(255, g))
            r = max(0, min(255, r))

            print("RGB Values:", r, g, b)

            color_name, hex_value = self.get_color_info(r, g, b)
            self.hex_value = hex_value

            label_text = 'Color Name: {}, R:{}, G:{}, B:{}'.format(color_name, r, g, b)
            print(label_text)

            self.color_info_label.text = label_text

            # Set the text color of the label to white if the sum of RGB values is greater than 600
            if r >= 165 and g >= 165 and b >= 165:
                self.color_info_label.theme_text_color = "Primary"
            else:
                self.color_info_label.theme_text_color = "Custom"
                self.color_info_label.text_color = [1, 1, 1, 1]

            # Set the background color of the label based on the RGB values
            self.color_info_label.background_color = [r / 255, g / 255, b / 255, 1]

            if self.rect is not None and self.rect in self.color_info_label.canvas.before.children:
                # Remove self.rect from canvas.before if it has been added previously
                self.color_info_label.canvas.before.remove(self.rect)

            with self.color_info_label.canvas.before:
                Color(r / 255.0, g / 255.0, b / 255.0, 1)  # Set the background color
                # Calculate the position to center the rectangle horizontally
                pos_x = self.color_info_label.center_x - self.color_info_label.width / 2
                pos_y = self.color_info_label.y
                # Create the Rectangle instruction with the calculated position and the size of the label
                self.rect = Rectangle(pos=(pos_x, pos_y),
                                      size=(self.color_info_label.width, self.color_info_label.height))

    def get_color_info(self, R, G, B):
        # Get color information from the loaded CSV file based on RGB values
        minimum = 15000
        color_info = {}
        for i in range(len(self.csv)):
            d = abs(R - int(self.csv.loc[i, "R"])) \
                + abs(G - int(self.csv.loc[i, "G"])) \
                + abs(B - int(self.csv.loc[i, "B"]))
            if d <= minimum:
                minimum = d
                color_info['color_name'] = self.csv.loc[i, "color_name"]
                color_info['hex_value'] = self.csv.loc[i, "hexa"]
        return color_info['color_name'], color_info['hex_value']

    def on_generate_matching_colors(self, instance):
        # Call a method to retrieve the selected color and generate matching colors
        hex_value = self.hex_value
        if hex_value:
            matching_colors = self.generate_matching_colors(hex_value)
            self.display_matching_colors_popup(matching_colors)

    def display_matching_colors_popup(self, matching_colors):
        # Display a popup with matching colors
        popup = Popup(title='Matching Colors', size_hint=(None, None), size=(300, 350))
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Remove all occurrences of #ffffff from matching_colors list
        matching_colors = [color for color in matching_colors if color != '#ffffff']

        num_colors_to_display = min(len(matching_colors), 5)
        for i in range(num_colors_to_display):
            color_hex = matching_colors[i]
            color_rgba = [int(color_hex[i:i + 2], 16) / 255.0 for i in (1, 3, 5)] + [1]  # Convert hex to RGBA
            color_rect = ColorRectangle(color=color_rgba, size_hint=(1, None), height=40)  # Pass RGBA color
            layout.add_widget(color_rect)

        popup.content = layout
        popup.open()

    def generate_matching_colors(self, hex_value):
        # Generate matching colors based on the input color
        input_color = hex_value
        num_colors = 5

        input_rgb = tuple(int(input_color[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        input_h, input_l, input_s = colorsys.rgb_to_hls(*input_rgb)

        matching_colors = []
        for i in range(num_colors):
            hue = (input_h + 0.1 * i) % 1.0
            lightness = min(1.0, max(0.0, input_l + 0.1 * i))
            saturation = min(1.0, max(0.0, input_s + 0.1 * i))

            new_rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
            new_hex = "#{:02x}{:02x}{:02x}".format(int(new_rgb[0] * 255), int(new_rgb[1] * 255),
                                                   int(new_rgb[2] * 255))

            matching_colors.append(new_hex)

        return matching_colors


if __name__ == '__main__':
    ColorDetectionApp().run()
