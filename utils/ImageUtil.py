import subprocess

from PIL import Image, ImageDraw, ImageFont
from vtracer import vtracer

from config import inkscape_path
from utils.image_convert.gcode_to_dat import convert_gcode_to_dat
from utils.image_convert.unicorn import convert_svg_to_gcode


def generate_image(text, output_path,image_width,image_height,offsetX,offsetY):
    # 设置图像大小和背景颜色
    # image_width = 1488
    # image_height = 1052
    background_color = (255, 255, 255)  # 白色

    # 创建白色背景图像
    image = Image.new('RGB', (image_width, image_height), background_color)

    # 获取一个字体
    font_size = 100
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # 创建绘图对象
    draw = ImageDraw.Draw(image)

    # 使用textbbox计算文本边界框以获取文本尺寸
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 计算文本大小和位置
    # text_width, text_height = draw.textsize(text, font=font)
    # print(f"Text size: {text_width}x{text_height}")
    text_x = ((image_width - text_width) / 2) + offsetX
    text_y = ((image_height - text_height) / 2) + offsetY

    # # 写入文本到图像中心
    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)  # 使用黑色填充文本
    image = image.rotate(90, expand=True)

    # 保存图像
    image.save(output_path)

# update by xiaojuzi 20240701
def generateH5WordGameDat(textToDraw, outPutFolder,fileName,imageWidth,imageHeight,offsetX,offsetY):

    # text_to_draw = "11 + 10 = 21"

    #生成对应的svg、gcode文件目录

    output_image_path = outPutFolder + f'/{fileName}.png'

    svg_file_path = outPutFolder + f'/{fileName}.svg'

    gcode_file_path =outPutFolder + f'/{fileName}.gcode'

    dat_file_path =outPutFolder + f'/{fileName}.dat'

    lrc_file_path =outPutFolder + f'/{fileName}.lrc'

    # 写入数据
    with open(lrc_file_path, 'w') as file:
        file.write('000000000000000000000000000000000')


    #生成算数图像
    generate_image(textToDraw, output_image_path,imageWidth,imageHeight,offsetX,offsetY)
    #转为dat文件
    vtracer.convert_image_to_svg_py(output_image_path, svg_file_path, colormode='binary')

    # # svg文件转gcode文件 xiaojuzi 20240527 测试终版
    command = [
        inkscape_path,
        svg_file_path,
        "--export-type=gcode",
        f"--export-filename={gcode_file_path}",
        '--actions=EditSelectAll;SelectionUnGroup;ExtensionIdPrefix(com.makerbot.unicorn.gcode);FileSave;FileClose'
    ]
    # 运行Inkscape命令
    subprocess.run(command)

    # #Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path,dat_file_path)


if __name__ == "__main__":
    text_to_draw = "1 + 1 = 2"
    output_image_path = "output_image.png"
    svg_file_path =  "output_image.svg"
    generate_image(text_to_draw, output_image_path,1052,744,0,296)
    vtracer.convert_image_to_svg_py(output_image_path, svg_file_path, colormode='binary')
    # print(f"Image generated and saved to {output_image_path}")

    # generateH5WordGameDat()
