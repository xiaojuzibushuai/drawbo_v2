#!/usr/bin/env python
'''
Copyright (c) 2010 MakerBot Industries

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
import sys,os
from math import *
from utils.image_convert import inkex
from utils.image_convert.context import GCodeContext
from utils.image_convert.svg_parser import SvgParser


class MyEffect(inkex.Effect):
  def __init__(self,outputPath:str):
    inkex.Effect.__init__(self)
    self.OptionParser.add_option("--pen-up-angle",
                      action="store", type="float",
                      dest="pen_up_angle", default="50.0",
                      help="Pen Up Angle")
    self.OptionParser.add_option("--pen-down-angle",
                      action="store", type="float",
                      dest="pen_down_angle", default="30.0",
                      help="Pen Down Angle")
    self.OptionParser.add_option("--start-delay",
                      action="store", type="float",
                      dest="start_delay", default="150.0",
                      help="Delay after pen down command before movement in milliseconds")
    self.OptionParser.add_option("--stop-delay",
                      action="store", type="float",
                      dest="stop_delay", default="150.0",
                      help="Delay after pen up command before movement in milliseconds")
    self.OptionParser.add_option("--xy-feedrate",
                      action="store", type="float",
                      dest="xy_feedrate", default="3500.0",
                      help="XY axes feedrate in mm/min")
    self.OptionParser.add_option("--z-feedrate",
                      action="store", type="float",
                      dest="z_feedrate", default="150.0",
                      help="Z axis feedrate in mm/min")
    self.OptionParser.add_option("--z-height",
                      action="store", type="float",
                      dest="z_height", default="0.0",
                      help="Z axis print height in mm")
    self.OptionParser.add_option("--finished-height",
                      action="store", type="float",
                      dest="finished_height", default="0.0",
                      help="Z axis height after printing in mm")
    self.OptionParser.add_option("--register-pen",
                      action="store", type="string",
                      dest="register_pen", default="true",
                      help="Add pen registration check(s)")
    self.OptionParser.add_option("--x-home",
                      action="store", type="float",
                      dest="x_home", default="0.0",
                      help="Starting X position")
    self.OptionParser.add_option("--y-home",
                      action="store", type="float",
                      dest="y_home", default="0.0",
                      help="Starting Y position")
    self.OptionParser.add_option("--num-copies",
                      action="store", type="int",
                      dest="num_copies", default="1")
    self.OptionParser.add_option("--continuous",
                      action="store", type="string",
                      dest="continuous", default="false",
                      help="Plot continuously until stopped.")
    self.OptionParser.add_option("--pause-on-layer-change",
                      action="store", type="string",
                      dest="pause_on_layer_change", default="false",
                      help="Pause on layer changes.")
    self.OptionParser.add_option("--tab",
                      action="store", type="string",
                      dest="tab")
    self.outputPath = outputPath

  def output(self):
    self.context.generate(self.outputPath)

  def effect(self):
    self.context = GCodeContext(self.options.xy_feedrate, self.options.z_feedrate, 
                           self.options.start_delay, self.options.stop_delay,
                           self.options.pen_up_angle, self.options.pen_down_angle,
                           self.options.z_height, self.options.finished_height,
                           self.options.x_home, self.options.y_home,
                           self.options.register_pen,
                           self.options.num_copies,
                           self.options.continuous,
                           self.svg_file)
    parser = SvgParser(self.document.getroot(), self.options.pause_on_layer_change)
    parser.parse()
    for entity in parser.entities:
      entity.get_gcode(self.context)


def convert_svg_to_gcode(inputPath: str,outputPath: str):
  e = MyEffect(outputPath)
  args =  [
    "--tab=pen_changes",
    "--pen-up-angle=50",
    "--pen-down-angle=30",
    "--start-delay=150",
    "--stop-delay=150",
    "--xy-feedrate=3500",
    "--z-feedrate=150",
    "--z-height=0",
    "--finished-height=0",
    "--register-pen=true",
    "--x-home=0",
    "--y-home=0",
    "--num-copies=1",
    "--continuous=false",
    "--pause-on-layer-change=true",
    inputPath
]
  e.affect(args=args)

if __name__ == '__main__':   #pragma: no cover
#   e = MyEffect()
#   args =  [
#     "--tab=pen_changes",
#     "--pen-up-angle=50",
#     "--pen-down-angle=30",
#     "--start-delay=150",
#     "--stop-delay=150",
#     "--xy-feedrate=3500",
#     "--z-feedrate=150",
#     "--z-height=0",
#     "--finished-height=0",
#     "--register-pen=true",
#     "--x-home=0",
#     "--y-home=0",
#     "--num-copies=1",
#     "--continuous=false",
#     "--pause-on-layer-change=true",
#     "./svg/hhh.svg"
# ]
#   e.affect(args=args)

  svg_dir = os.path.join(os.getcwd(),"utils","image_convert","svg","hhh.svg")
  gcode_dir = os.path.join(os.getcwd(),"utils","image_convert","gcode","hhh.gcode")
  convert_svg_to_gcode("./svg/bbb.svg","./gcode/bbb.gcode")
