import logging
import subprocess
from typing import Iterable, List, Tuple, Union
import matplotlib.pyplot as plt
import cv2
import numpy as np
import vtracer

from config import inkscape_path
from utils.image_convert.gcode_to_dat import convert_gcode_to_dat
from utils.image_convert.png_to_svg import cv_png_to_svg, cv_camera_png_to_svg
from utils.image_convert.unicorn import convert_svg_to_gcode

import xml.etree.ElementTree as ET


#xiaojuzi 2023111
def convert_png_to_svg(png_file_path, svg_file_path):
    try:
        cv_png_to_svg(png_file_path, svg_file_path)
    except Exception as e:
        print('面板图片转SVG文件时出现异常:', str(e))
        logging.info('图片转SVG文件时出现异常:', str(e))

#20231118 xiaojuzi v2
def convert_camera_png_to_svg(png_file_path, svg_file_path):
    try:
        cv_camera_png_to_svg(png_file_path, svg_file_path)
    except Exception as e:
        print('摄像头图片转SVG文件时出现异常:', str(e))
        logging.info('图片转SVG文件时出现异常:', str(e))

def svg_to_gcode(svg_file_path,gcode_file_path):
    try:
        convert_svg_to_gcode(svg_file_path, gcode_file_path)
    except Exception as e:
        print('SVG文件转gcode文件时出现异常:', str(e))
        logging.info('SVG文件转gcode文件时出现异常:', str(e))

def gcode_to_dat(gcode_file_path,dat_file_path):
    try:
        convert_gcode_to_dat(gcode_file_path, dat_file_path)
    except Exception as e:
        print('Gcode文件转Dat文件时出现异常:', str(e))
        logging.info('Gcode文件转Dat文件时出现异常:', str(e))

def convert_image_to_dat(png_file_path,svg_file_path,gcode_file_path,dat_file_path):

    #1、图片转svg文件
    convert_png_to_svg(png_file_path,svg_file_path)

    #2、svg文件转Gcode文件
    svg_to_gcode(svg_file_path,gcode_file_path)

    #3、Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path,dat_file_path)

def convert_camera_image_to_dat(png_file_path,svg_file_path,gcode_file_path,dat_file_path):

    #1、图片转svg文件
    convert_camera_png_to_svg(png_file_path,svg_file_path)

    #2、svg文件转Gcode文件
    svg_to_gcode(svg_file_path,gcode_file_path)

    #3、Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path,dat_file_path)


#预处理图片 20231122   update by xiaojuzi 20240102 加入旋转
def pre_convert_png_to_svg(rotate,png_file_path, svg_file_path):
    try:
        # pre_cv_png_to_svg(png_file_path, png_file_path)

        # vtracer.convert_image_to_svg_py(png_file_path, svg_file_path, colormode='binary')

        cv_png_to_svg(rotate,png_file_path, svg_file_path)

    except Exception as e:
        print('面板图片转SVG文件时出现异常:', str(e))
        logging.info('图片转SVG文件时出现异常:', str(e))


def temp_convert_svg_to_gcode(svg_file_path, gcode_file_path):
    try:
        # 创建Inkscape命令
        command = f'{inkscape_path} {svg_file_path} --export-type=gcode --export-filename={gcode_file_path} --actions="EditSelectAll;SelectionUnGroup;ExtensionIdPrefix(com.makerbot.unicorn.gcode);FileSave;FileClose"'
        # 运行Inkscape命令
        subprocess.run(command, shell=True)
    except Exception as e:
        print('SVG文件转gcode文件时出现异常:', str(e))
        logging.info('SVG文件转gcode文件时出现异常:', str(e))


def test_convert_image_to_dat(rotate,png_file_path,svg_file_path,gcode_file_path,dat_file_path):

    #1、图片转svg文件
    pre_convert_png_to_svg(rotate,png_file_path,svg_file_path)

    #2、svg文件转Gcode文件
    # svg_to_gcode(svg_file_path,gcode_file_path)

    # svg文件转gode文件 xiaojuzi 20240527 测试终版
    temp_convert_svg_to_gcode(svg_file_path, gcode_file_path)

    #3、Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path,dat_file_path)

def convert_simple_image_to_dat(png_file_path,svg_file_path,gcode_file_path,dat_file_path):
    # 1、图片转svg文件
    bitmap_to_contour_svg(png_file_path,svg_file_path)

    # 2、svg文件转Gcode文件
    svg_to_gcode(svg_file_path, gcode_file_path)

    # 3、Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path, dat_file_path)

def look_shape(a: Iterable) -> Tuple:
    # for debug
    return np.array(a).shape


def length_within_points(a: Iterable, empty_value: Union[int, float] = 0) -> int:
    """
        a simple instance:
            array : [empty_value, empty_value, empty_value, 1, empty_value, 0, 1, 2, empty_value]
            Then length_within_points(array) will return index diff between 1 and 2, which is 5
    """
    a = list(a)
    l_pivot, r_pivot = -1, -2
    for index, (l_val, r_val) in enumerate(zip(a[::1], a[::-1])):
        if l_val != empty_value and l_pivot == -1:
            l_pivot = index
        if r_val != empty_value and r_pivot == -2:
            r_pivot = len(a) - index

    return r_pivot - l_pivot + 1


def dump_rings_from_image(image: np.ndarray, output_path: str, plot_dict: dict = {"color": "k", "linewidth": 1.5},
                          default_height: float = 12) -> List[np.ndarray]:

    blur = cv2.GaussianBlur(image, (3, 3), 0)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    edge = cv2.Canny(gray, 50, 150)

    valid_width = length_within_points(edge.sum(axis=0))
    valid_height = length_within_points(edge.sum(axis=1))
    true_ratio = valid_width / valid_height

    contour_tuple = cv2.findContours(edge, mode=cv2.RETR_TREE, method=cv2.CHAIN_APPROX_NONE)
    contours = contour_tuple[0]
    rings = [np.array(c).reshape([-1, 2]) for c in contours]

    max_x, max_y, min_x, min_y = 0, 0, 0, 0
    for ring in rings:
        max_x = max(max_x, ring.max(axis=0)[0])
        max_y = max(max_y, ring.max(axis=0)[1])
        min_x = max(min_x, ring.min(axis=0)[0])
        min_y = max(min_y, ring.min(axis=0)[1])

    plt.figure(figsize=[default_height * true_ratio, default_height])

    for _, ring in enumerate(rings):
        close_ring = np.vstack((ring, ring[0]))
        xx = close_ring[..., 0]
        yy = max_y - close_ring[..., 1]
        plt.plot(xx, yy, **plot_dict)

    plt.axis("off")
    plt.savefig(output_path,transparent=True)


def bitmap_to_contour_svg(input_bitmap_path: str, output_svg_path: str):
    img = cv2.imread(input_bitmap_path)
    dump_rings_from_image(img, output_path=output_svg_path)

    # 定义命令 0.84 本地用
    inkscape_path = "E:/Inkscape1.1.2/bin/inkscape.exe"
    # command = f'{inkscape_path} {output_svg_path} --verb=EditSelectAll --verb=SelectionSimplify --verb=FileSave --verb=FileClose'
    # 线上命令用
    # inkscape_path = 'inkscape'
    command = f'{inkscape_path} {output_svg_path} --batch-process --actions="EditSelectAll;SelectionSimplify;FileSave;FileClose"'
    # 执行命令
    subprocess.run(command, shell=True)

    removeXml(output_svg_path)

def removeXml(input):

    # 读取SVG文件
    tree = ET.parse(input)
    root = tree.getroot()

    # 收集要删除的元素
    elements_to_remove = []

    # 找到所有的g元素
    for group in root.findall('.//{http://www.w3.org/2000/svg}g'):
        group_id = group.get('id')

        # 判断id是否符合特定模式
        if group_id is not None and group_id.startswith('line2d_'):
            # 获取i的值
            i = int(group_id.split('_')[-1])

            # 判断i是偶数
            if i % 2 == 0:
                elements_to_remove.append(group)

    # 删除收集到的元素
    for element in elements_to_remove:
        # 找到要删除元素的父节点
        for parent in root.iter():
            if element in parent:
                parent.remove(element)
                break

    # 将修改后的 XML 写回原始文件
    tree.write(input, xml_declaration=False, method="xml", encoding='utf-8')



if __name__ == "__main__":
    png_file_path = 'ceshi1.png'
    svg_file_path = 'ceshi1.svg'
    gcode_file_path = 'ceshi1.gcode'
    dat_file_path = 'ceshi1.dat'


    # convert_image_to_dat(png_file_path, svg_file_path, gcode_file_path, dat_file_path)

    # vtracer.convert_image_to_svg_py(png_file_path, svg_file_path, colormode='binary')
    # convert_simple_image_to_dat(png_file_path, svg_file_path, gcode_file_path, dat_file_path)
    test_convert_image_to_dat(0,png_file_path, svg_file_path, gcode_file_path, dat_file_path)
