import re
import os

def convert_gcode_to_dat(gcode_file_path, dat_file_path):
    enable_out_flag = 0

    S_Layer_x = 32762
    S_Pen = 32763
    Pen_Up = 0
    Pen_Down = 1
    S_Data = 32764
    Data_End = 1

    with open(gcode_file_path, 'r') as gcode_file, open(dat_file_path, 'wb') as dat_file:
        for line in gcode_file:
            line = line.strip()
            # print(line)

            if line.startswith("M300 S30 "):  # pen down
                if enable_out_flag != 0:
                    num = S_Pen
                    dat_file.write(num.to_bytes(2, 'little',signed=True))
                    num1 = Pen_Down
                    dat_file.write(num1.to_bytes(2, 'little',signed=True))

            elif line.startswith("M300 S50 "):  # pen up
                num = S_Pen
                dat_file.write(num.to_bytes(2, 'little',signed=True))
                num1 = Pen_Up
                dat_file.write(num1.to_bytes(2, 'little',signed=True))

            elif line.startswith(("M91 ","G91 ")):  # data end

                num = S_Data

                dat_file.write(num.to_bytes(2, 'little', signed=True))
                num1 = Data_End
                dat_file.write(num1.to_bytes(2, 'little', signed=True))

                dat_file.write(num.to_bytes(2, 'little', signed=True))
                dat_file.write(num1.to_bytes(2, 'little', signed=True))

                break

            elif line.startswith("Layer"):
                enable_out_flag = 1
                line = re.sub(r"Layer\s*", "", line)
                a = int(line)
                num = S_Layer_x
                dat_file.write(num.to_bytes(2, 'little',signed=True))
                dat_file.write(a.to_bytes(2, 'little',signed=True))

            else:
                match = re.match(r"G1 X(\S+) Y(\S+)", line)
                if match:
                    x = int(float(match.group(1)) / 0.0235)
                    y = int(float(match.group(2)) / 0.0235)
                    if x != 0 and y != 0:
                        dat_file.write(x.to_bytes(2, 'little', signed=True))
                        dat_file.write(y.to_bytes(2, 'little', signed=True))

        num = S_Data
        dat_file.write(num.to_bytes(2, 'little', signed=True))
        num1 = Data_End
        dat_file.write(num1.to_bytes(2, 'little', signed=True))


        dat_file.write(num.to_bytes(2, 'little', signed=True))

        dat_file.write(num1.to_bytes(2, 'little', signed=True))



if __name__=='__main__':
    gcode_dir = os.path.join(os.getcwd(),"utils","image_convert","gcode","hhh.gcode")
    dat_dir = os.path.join(os.getcwd(),"utils","image_convert","dat","hhh.dat")
    convert_gcode_to_dat("./gcode/bbb.gcode","./dat/bbb.dat")