import io as _io
import PIL.Image as _image
import PIL.ImageTk as _imageTk

__all__ = ["is_image", "create_thumbnail", "get_photo_image"]
_thumbnail_height = 350


def is_image(filename):
    try:
        img = _image.open(filename)
        img.verify()
        return True
    except:
        return False


def create_thumbnail(filename):
    img = _image.open(filename)
    width = int(_thumbnail_height * img.width / img.height)
    img.thumbnail((width, _thumbnail_height), _image.ANTIALIAS)

    result = _io.BytesIO()
    img.save(result, format="PNG")
    data = result.getvalue()
    return data


def get_photo_image(data):
    img = _image.open(_io.BytesIO(data))
    return _imageTk.PhotoImage(img)
