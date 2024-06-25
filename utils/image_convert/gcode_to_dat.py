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


def merge_gcode_files(input_files, output_file):
    with open(output_file, 'w') as output:
        for idx, file_path in enumerate(input_files):
            with open(file_path, 'r') as file:
                file_content = file.readlines()

                if idx == 0:
                    # For the first file, write until the first "(end of print job)"
                    end_of_print_job_index = next((i for i, line in enumerate(file_content) if '(end of print job)' in line), None)
                    print(end_of_print_job_index)
                    if end_of_print_job_index is not None:
                        output.writelines(file_content[:end_of_print_job_index + 1])
                    else:
                        return None
                elif idx == len(input_files) - 1:
                    # For the last file, write everything until the end of the file
                    polyline_index = next((i for i, line in enumerate(file_content) if '(Polyline consisting of 1 segments.)' in line), None)
                    print(polyline_index)
                    if polyline_index is not None:
                        output.writelines(file_content[polyline_index:])
                    else:
                        return None

                else:
                    # For subsequent files, find "(Polyline consisting of 1 segments.)" and write until "(end of print job)"
                    polyline_index = next((i for i, line in enumerate(file_content) if '(Polyline consisting of 1 segments.)' in line), None)
                    if polyline_index is not None:
                        end_of_print_job_index = next((i for i, line in enumerate(file_content) if '(end of print job)' in line and i > polyline_index), None)
                        if end_of_print_job_index is not None:
                            print(polyline_index,end_of_print_job_index)
                            output.writelines(file_content[polyline_index:end_of_print_job_index + 1])
                        else:
                            return None
                    else:
                        return None

    print(f'Merged {len(input_files)} gcode files successfully. Merged content saved to {output_file}')


if __name__=='__main__':

    input_files = [
        '1.gcode',
        '2.gcode',
        '3.gcode'
        # Add more files as needed
    ]

    output_file = 'merged_output.gcode'
    merge_gcode_files(input_files, output_file)

    # convert_gcode_to_dat(output_file,'out_merged.dat')

    # gcode_dir = os.path.join(os.getcwd(),"utils","image_convert","gcode","hhh.gcode")
    # dat_dir = os.path.join(os.getcwd(),"utils","image_convert","dat","hhh.dat")
    # convert_gcode_to_dat("./gcode/bbb.gcode","./dat/bbb.dat")