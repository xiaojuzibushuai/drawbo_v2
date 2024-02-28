import logging

import vtracer
from utils.image_convert.gcode_to_dat import convert_gcode_to_dat
from utils.image_convert.png_to_svg import cv_png_to_svg, cv_camera_png_to_svg
from utils.image_convert.unicorn import convert_svg_to_gcode


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
def test_convert_image_to_dat(rotate,png_file_path,svg_file_path,gcode_file_path,dat_file_path):

    #1、图片转svg文件
    pre_convert_png_to_svg(rotate,png_file_path,svg_file_path)

    #2、svg文件转Gcode文件
    svg_to_gcode(svg_file_path,gcode_file_path)

    #3、Gcode文件转Dat文件
    convert_gcode_to_dat(gcode_file_path,dat_file_path)


if __name__ == "__main__":
    png_file_path = '2.png'
    svg_file_path = 'test.svg'
    gcode_file_path = 'test.gcode'
    dat_file_path = 'test.dat'


    test_convert_image_to_dat(1,png_file_path, svg_file_path, gcode_file_path, dat_file_path)
