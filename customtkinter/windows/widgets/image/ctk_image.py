import io
import tkinter as tk
from typing import Tuple, Dict, Callable, List

try:
    from PIL import Image
except (ImportError, OSError):
    Image = None

try:
    from PIL import ImageTk
except (ImportError, OSError):
    ImageTk = None

if ImageTk is None and Image is not None:
    class _FallbackPhotoImage(tk.PhotoImage):
        def __init__(self, pil_image):
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            super().__init__(data=buf.getvalue())

    class ImageTk:
        PhotoImage = _FallbackPhotoImage


class CTkImage:
    """
    Class to store one or two PIl.Image.Image objects and display size independent of scaling:

    light_image: PIL.Image.Image for light mode
    dark_image: PIL.Image.Image for dark mode
    size: tuple (<width>, <height>) with display size for both images

    One of the two images can be None and will be replaced by the other image.
    """

    _checked_PIL_import = False

    def __init__(self,
                 light_image: "Image.Image" = None,
                 dark_image: "Image.Image" = None,
                 size: Tuple[int, int] = (20, 20)):

        if not self._checked_PIL_import:
            self._check_pil_import()

        self._light_image = light_image
        self._dark_image = dark_image
        self._check_images()
        self._size = size

        self._configure_callback_list: List[Callable] = []
        self._scaled_light_photo_images: Dict[Tuple[int, int], ImageTk.PhotoImage] = {}
        self._scaled_dark_photo_images: Dict[Tuple[int, int], ImageTk.PhotoImage] = {}

    @classmethod
    def _check_pil_import(cls):
        cls._checked_PIL_import = True

    def _to_tk_photo(self, img_obj, scaled_size: Tuple[int, int]) -> tk.PhotoImage:
        resized = img_obj.resize(scaled_size) if hasattr(img_obj, "resize") else img_obj
        if hasattr(resized, "to_photo_image"):
            return resized.to_photo_image()
        if ImageTk is not None:
            return ImageTk.PhotoImage(resized)
        buf = io.BytesIO()
        resized.save(buf, format="PNG")
        return tk.PhotoImage(data=buf.getvalue())

    def add_configure_callback(self, callback: Callable):
        """ add function, that gets called when image got configured """
        self._configure_callback_list.append(callback)

    def remove_configure_callback(self, callback: Callable):
        """ remove function, that gets called when image got configured """
        self._configure_callback_list.remove(callback)

    def configure(self, **kwargs):
        if "light_image" in kwargs:
            self._light_image = kwargs.pop("light_image")
            self._scaled_light_photo_images = {}
            self._check_images()

        if "dark_image" in kwargs:
            self._dark_image = kwargs.pop("dark_image")
            self._scaled_dark_photo_images = {}
            self._check_images()

        if "size" in kwargs:
            self._size = kwargs.pop("size")

        # call all functions registered with add_configure_callback()
        for callback in self._configure_callback_list:
            callback()

    def cget(self, attribute_name: str) -> any:
        if attribute_name == "light_image":
            return self._light_image
        elif attribute_name == "dark_image":
            return self._dark_image
        elif attribute_name == "size":
            return self._size

    def _check_images(self):
        # check values
        if self._light_image is None and self._dark_image is None:
            raise ValueError("CTkImage: No image given, light_image is None and dark_image is None.")

        # check sizes
        if self._light_image is not None and self._dark_image is not None and getattr(self._light_image, "size", None) != getattr(self._dark_image, "size", None):
            raise ValueError(f"CTkImage: light_image size {self._light_image.size} must be the same as dark_image size {self._dark_image.size}.")

    def _get_scaled_size(self, widget_scaling: float) -> Tuple[int, int]:
        return round(self._size[0] * widget_scaling), round(self._size[1] * widget_scaling)

    def _get_scaled_light_photo_image(self, scaled_size: Tuple[int, int]) -> tk.PhotoImage:
        if scaled_size in self._scaled_light_photo_images:
            return self._scaled_light_photo_images[scaled_size]
        else:
            self._scaled_light_photo_images[scaled_size] = self._to_tk_photo(self._light_image, scaled_size)
            return self._scaled_light_photo_images[scaled_size]

    def _get_scaled_dark_photo_image(self, scaled_size: Tuple[int, int]) -> tk.PhotoImage:
        if scaled_size in self._scaled_dark_photo_images:
            return self._scaled_dark_photo_images[scaled_size]
        else:
            self._scaled_dark_photo_images[scaled_size] = self._to_tk_photo(self._dark_image, scaled_size)
            return self._scaled_dark_photo_images[scaled_size]

    def create_scaled_photo_image(self, widget_scaling: float, appearance_mode: str) -> "ImageTk.PhotoImage":
        scaled_size = self._get_scaled_size(widget_scaling)

        if appearance_mode == "light" and self._light_image is not None:
            return self._get_scaled_light_photo_image(scaled_size)
        elif appearance_mode == "light" and self._light_image is None:
            return self._get_scaled_dark_photo_image(scaled_size)

        elif appearance_mode == "dark" and self._dark_image is not None:
            return self._get_scaled_dark_photo_image(scaled_size)
        elif appearance_mode == "dark" and self._dark_image is None:
            return self._get_scaled_light_photo_image(scaled_size)


