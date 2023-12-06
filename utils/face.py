import face_recognition
from PIL import Image, ImageDraw
import base64
from io import BytesIO

class FaceTool:
    image_resize = (400, 400)
    first_face_location = []
    image_instance = None
    d_type = 1  # 默认为一代 1是第一代设备需要截取400X400像素 2是第二代设备保持原图片

    def __init__(self, image_path, d_type=1, add_px=0):
        self.image_path = image_path
        self.face_image = face_recognition.load_image_file(self.image_path)
        face_locations = face_recognition.face_locations(self.face_image)
        first_face_location = face_locations[0] if face_locations else []
        self.first_face_location = list(first_face_location)
        self.d_type = d_type
        if add_px and isinstance(add_px, int):
            self.first_face_location[0] = self.first_face_location[0] - add_px
            self.first_face_location[1] = self.first_face_location[1] + add_px
            self.first_face_location[2] = self.first_face_location[2] + add_px
            self.first_face_location[3] = self.first_face_location[3] - add_px
        self.img = Image.fromarray(self.face_image, 'RGB')

    def red_token(self):
        self.image_instance = self.img.copy()
        if self.first_face_location:
            img_with_red_box_draw = ImageDraw.Draw(self.image_instance)
            img_with_red_box_draw.rectangle([
                (self.first_face_location[3], self.first_face_location[0]),
                (self.first_face_location[1], self.first_face_location[2])
            ], outline='red', width=3)

    def crop_face(self):
        self.image_instance = self.img.copy()
        # 裁剪出检测到的人脸
        if self.first_face_location:
            if self.d_type == 1:
                self.image_instance = self.image_instance.crop((
                    self.first_face_location[3],  # Left x
                    self.first_face_location[0],  # Top y
                    self.first_face_location[1],  # Right x
                    self.first_face_location[2]   # Bottom y
                ))
            return True
        else:
            return False

    def face_show(self):
        if self.image_instance:
            self.image_instance.show()
            return True
        else:
            return False

    def save(self, image_path):
        if self.image_instance:
            self.image_instance.save(image_path)
            return True
        else:
            return False

    def face_to_base64(self):
        # 放大图像到400X400
        if self.d_type == 1:
            self.image_instance = self.image_instance.resize(self.image_resize)
        output_buffer = BytesIO()
        self.image_instance.save(output_buffer, format='JPEG')
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data)
        return base64_str


if __name__ == '__main__':
    ft = FaceTool('face_test/face_4.jpg')
    if ft.crop_face():
        print(ft.face_to_base64())
    else:
        print('未检测到人脸')
