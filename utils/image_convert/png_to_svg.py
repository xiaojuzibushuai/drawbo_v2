import logging
import os
import subprocess

import vtracer
from PIL import Image
import cv2 as cv
import numpy as np
from lxml import etree

from config import inkscape_path


# input_path = "./png/bbb.png"
# output_path = "./svg/bbb.svg"

# Minimal example: use all default values, generate a multicolor SVG
# vtracer.convert_image_to_svg_py(input_path, output_path)

# Single-color example. Good for line art, and much faster than full color:
# vtracer.convert_image_to_svg_py(input_path, output_path, colormode='binary')


# All the bells & whistles
# vtracer.convert_image_to_svg_py(input_path,
#                                 output_path,
#                                 colormode = 'color',        # ["color"] or "binary"
#                                 hierarchical = 'stacked',   # ["stacked"] or "cutout"
#                                 mode = 'spline',            # ["spline"] "polygon", or "none"
#                                 filter_speckle = 4,         # default: 4
#                                 color_precision = 6,        # default: 6
#                                 layer_difference = 16,      # default: 16
#                                 corner_threshold = 60,      # default: 60
#                                 length_threshold = 4.0,     # in [3.5, 10] default: 4.0
#                                 max_iterations = 10,        # default: 10
#                                 splice_threshold = 45,      # default: 45
#                                 path_precision = 3          # default: 8
#                                 )

def remove_black_border(image):
    # 获取图像大小
    width, height = image.size

    # 获取像素数据
    pixels = image.load()

    # 初始化边框颜色
    border_color = (0, 0, 0)  # 黑色

    # 检测上边框
    top_border = 0
    for y in range(height):
        if not all(pixels[x, y] == border_color for x in range(width)):
            top_border = y
            break

    # 检测下边框
    bottom_border = height - 1
    for y in range(height - 1, -1, -1):
        if not all(pixels[x, y] == border_color for x in range(width)):
            bottom_border = y
            break

    # 检测左边框
    left_border = 0
    for x in range(width):
        if not all(pixels[x, y] == border_color for y in range(height)):
            left_border = x
            break

    # 检测右边框
    right_border = width - 1
    for x in range(width - 1, -1, -1):
        if not all(pixels[x, y] == border_color for y in range(height)):
            right_border = x
            break

    # 裁剪图像，去除黑色边框
    cropped_image = image.crop((left_border, top_border, right_border + 1, bottom_border + 1))
    return cropped_image

#20231118 xiaojuzi v2
def cv_camera_png_to_svg(png_file_path, svg_file_path):

    image = cv.imread(png_file_path, cv.IMREAD_GRAYSCALE)

    binary = cv.adaptiveThreshold(image, 255,
                                  cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 25, 15)
    se = cv.getStructuringElement(cv.MORPH_RECT, (1, 1))
    se = cv.morphologyEx(se, cv.MORPH_CLOSE, (2, 2))
    mask = cv.dilate(binary, se)

    mask1 = cv.bitwise_not(mask)
    binary = cv.bitwise_and(image, mask)
    result = cv.add(binary, mask1)

    temp_png_file_path = os.path.abspath(png_file_path.split('.')[0]) +"_temp.png"

    #切图像
    cropped = result[int(result.shape[0]*0.15):int(result.shape[0]*0.85),int(result.shape[1]*0.1):int(result.shape[1]*0.9)]

    #旋转
    rotated_image = cv.rotate(cropped,cv.ROTATE_90_COUNTERCLOCKWISE)

    cv.imwrite(temp_png_file_path, rotated_image)

    # 调用函数进行图片分辨率统一
    resize_images(temp_png_file_path,(720,1280))

    vtracer.convert_image_to_svg_py(temp_png_file_path, svg_file_path, colormode='binary')

def resize_images(file_path, target_resolution):
    # 打开图片
    image = Image.open(file_path)

    # 获取原始分辨率
    original_resolution = image.size

    # logging.info("原始分辨率："+str(original_resolution))

    # 计算调整比例
    ratio = min(target_resolution[0] / original_resolution[0], target_resolution[1] / original_resolution[1])

    # 计算调整后的尺寸
    resized_size = (int(original_resolution[0] * ratio), int(original_resolution[1] * ratio))

    # 调整图片分辨率
    resized_image = image.resize(resized_size)

    # 创建空白画布
    canvas = Image.new('RGB', target_resolution, (255, 255, 255))

    # 在画布上居中粘贴调整后的图片
    offset = ((target_resolution[0] - resized_size[0]) // 2, (target_resolution[1] - resized_size[1]) // 2)
    canvas.paste(resized_image, offset)

    # 保存调整后的图片
    canvas.save(file_path)

def set_svg_document_properties(input_svg, output_svg, svg_width, svg_height,image_width,image_height, unit='px'):
    # 解析输入的 SVG 文件
    tree = etree.parse(input_svg)
    root = tree.getroot()

    # 设置宽度、高度和单位
    root.set('width', f'{svg_width}{unit}')
    root.set('height', f'{svg_height}{unit}')

    # 设置 viewBox
    viewBox = f'0 0 {svg_width} {svg_height}'
    root.set('viewBox', viewBox)

    # 找到 image 元素
    image_element = root.find(".//{http://www.w3.org/2000/svg}image")

    """
    进行单位换算 设置的为px  px转->mm 为：
    mm = ( px / DPI ) X 25.4
    px = ( mm / 25.4 ) X DPI 
  
    """
    new_image_width = int(image_width / 96 * 25.4)
    new_image_height = int(image_height / 96 * 25.4)

    #方框区域调试此偏移 20240527 xiaojuzi
    new_x = ((svg_width - new_image_width) / 2 ) - 15
    new_y = ((svg_height - new_image_height) / 2 ) - 30
    # print(new_x,new_y)

    # 修改 image 元素的 width 和 height 属性为
    image_element.set("width", str(image_width))
    image_element.set("height", str(image_height))

    # 设置 image 元素的新位置
    # 计算居中位置
    # 获取 SVG 文件的宽度和高度
    # 获取 image 元素的宽度和高度

    image_element.set("x", str(new_x))
    image_element.set("y", str(new_y))

    # 保存修改后的 SVG 文件
    tree.write(output_svg, pretty_print=False, xml_declaration=False, encoding='UTF-8')

# 20240102 xiaojuzi v2 修改 旋转角度
def cv_png_to_svg(rotate,png_file_path, svg_file_path):

    image = cv.imread(png_file_path, cv.IMREAD_GRAYSCALE)

    binary = cv.adaptiveThreshold(image, 255,
                                  cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY_INV, 25, 15)
    se = cv.getStructuringElement(cv.MORPH_RECT, (1, 1))
    se = cv.morphologyEx(se, cv.MORPH_CLOSE, (2, 2))
    mask = cv.dilate(binary, se)

    mask1 = cv.bitwise_not(mask)
    binary = cv.bitwise_and(image, mask)
    result = cv.add(binary, mask1)

    temp_png_file_path = os.path.abspath(png_file_path.split('.')[0]) + "_temp.png"

    # 旋转
    if int(rotate) == 1:
        rotated_image = cv.rotate(result, cv.ROTATE_90_CLOCKWISE)
    elif int(rotate) == 2:
        rotated_image = cv.rotate(result, cv.ROTATE_180)
    elif int(rotate) == 3:
        rotated_image = cv.rotate(result, cv.ROTATE_90_COUNTERCLOCKWISE)
    else:
        rotated_image = result

    cv.imwrite(temp_png_file_path, rotated_image)

    # 调用函数进行图片分辨率统一
    # resize_images(temp_png_file_path,(360,360))

    #xiaojuzi 20240527 测试终版 shell=True
    subprocess.run(
        [inkscape_path,temp_png_file_path,f"--export-filename={svg_file_path}"])

    # # # 设置 SVG 文件的文档属性
    set_svg_document_properties(svg_file_path, svg_file_path, 250, 353, 100, 100, "mm")

    subprocess.run(
        [inkscape_path, "--export-type=png", "-o", temp_png_file_path, "--export-background=#FFFFFF", svg_file_path])

    vtracer.convert_image_to_svg_py(temp_png_file_path, svg_file_path, colormode='binary')





if __name__ == "__main__":
    # png_dir = os.path.join(os.getcwd(),"utils","image_convert","png","hhh.png")

    png_file_path = '44.png'

    svg_file_path = '44.svg'

    # temp_png_file_path = os.path.dirname(os.path.abspath(png_file_path)) +"_temp.png"

    # cv_camera_png_to_svg(png_file_path, svg_file_path)
    cv_png_to_svg(0, png_file_path, svg_file_path)

    # svg_dir = os.path.join(os.getcwd(),"utils","image_convert","svg","hhh.svg")
    # convert_png_to_svg(input_path, output_path)