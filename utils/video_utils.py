import json
import logging
import multiprocessing
import os
import shutil
import subprocess


# xiaojuzi video工具类 v2 20231230

#检查视频时长是否一致 xiaojuzi 20231230
def check_video_time(ffprobe_path,source, target):

    source_time = get_video_duration(ffprobe_path,source)

    # print(source_time)

    if not source_time:
        return False

    format_source_time = float("{:.1f}".format(source_time))
    # print(format_source_time)

    target_time = get_video_duration(ffprobe_path,target)
    # print(target_time)
    # 取出时分秒
    if int(format_source_time) == int(target_time):
        # print("视频时长一致")
        return True
    else:
        # print("视频时长不一致")
        return False

#获取ts列表 xiaojuzi 20231230
def get_ts_list(output_path):

    fileList = []
    tsList = []
    m3u8file_path = output_path
    bottomline = ""
    try:
        with open(m3u8file_path, 'r') as f:
            for line in f:
                bottomline = line.strip()
                if bottomline.endswith(".ts"):
                    tsList.append(bottomline)
    except IOError as e:
        print(e)
    if "#EXT-X-ENDLIST" in bottomline:
        fileList.extend(tsList)
        return fileList
    return None

#获取视频时长 xiaojuzi 20231230
def get_video_duration(ffprobe_path,input_file):

    command = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        input_file
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout
        data = json.loads(output)
        print(data)
        duration = float(data['format']['duration'])
        # print(duration)
        return duration
    except subprocess.CalledProcessError as e:
        print(e)
        return 0

#将视频文件分片并加密 xiaojuzi 20231230
def generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path):

    ffmpeg_path = ffmpeg_path.replace('\\','/')
    ffprobe_path = ffprobe_path.replace('\\','/')
    video_path = video_path.replace('\\','/')
    output_path = output_path.replace('\\','/')

    keyinfo = os.path.join(os.path.dirname(output_path), 'keyinfo.txt').replace("\\", "/")
    with open(keyinfo, 'w') as f:
        f.write(os.path.join(os.path.dirname(output_path), 'encrypt.key').replace("\\", "/") + '\n')
        f.write(os.path.join(os.path.dirname(output_path), 'encrypt.key').replace("\\", "/") + '\n')
        f.write('8c8f033870dc07570b8b74c6267f6564' + '\n')

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 获取服务器CPU数目
    cpu_count = multiprocessing.cpu_count()
    # print(cpu_count)

    m3u8folder_path = output_path
    m3u8_name = 'slice.m3u8'
    encrypted_m3u8_name ='encrypted_slice.m3u8'

    # 使用FFmpeg生成M3U8文件
    command = [
        ffmpeg_path,
        '-i', video_path,
        '-c:v', 'libx264',#对视频编码
        '-c:a', 'copy',#对音频复制
        '-f', 'hls',#生成hls
        '-hls_time', '10',
        '-hls_list_size', '0',#设置hls播放列表
        '-threads', str(cpu_count),#多处理器
        '-hls_playlist_type', 'vod',#点播
        # '-hls_key_info_file', 'keyinfo.txt',#秘钥文件
        '-hls_segment_filename', os.path.join(m3u8folder_path, 'slice_%05d.ts').replace("\\", "/"),#生成ts文件
        os.path.join(m3u8folder_path, m3u8_name).replace("\\", "/")
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(e)

    # 检查视频时长
    check_time = check_video_time(ffprobe_path,video_path, os.path.join(m3u8folder_path, m3u8_name))
    if not check_time:
        # logging.info("Failed: Video duration check failed.")
        print("Failed: Video duration check failed.")
        return False,None
    print("Success: Video duration check passed.")

    # 检查M3U8列表
    ts_list = get_ts_list(os.path.join(m3u8folder_path, m3u8_name))

    if ts_list is None:
        # logging.info("Failed: M3U8 playlist check failed.")
        print("Failed: M3U8 playlist check failed.")
        return False,None
    # print(ts_list)

    #对上传正确的视频进行加密
    for ts_file in ts_list:
        ts_file_path = os.path.join(m3u8folder_path, ts_file).replace("\\", "/")
        # temp = ts_file.split('.')[0]

        command = [
            ffmpeg_path,
            '-i', ts_file_path,
            '-c:v', 'libx264',  # 对视频编码
            '-c:a', 'copy',  # 对音频复制
            # '-hls_key_info_file', 'keyinfo.txt',  # 秘钥文件
            '-hls_key_info_file', keyinfo,  # 秘钥文件
            '-f', 'hls',  # 生成hls
            '-hls_time', '24',
            '-hls_list_size', '0',  # 设置hls播放列表
            '-threads', str(cpu_count),  # 多处理器
            '-hls_playlist_type', 'vod',  # 点播
            '-hls_segment_filename', os.path.join(m3u8folder_path, f'encrypt_slice_%05d.ts').replace("\\", "/"),
            '-hls_flags', 'append_list',  # 追加到现有的播放列表
            os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/")
        ]
        try:
            subprocess.run(command)

        except subprocess.CalledProcessError as e:
            print(e)

    # 检查M3U8列表
    ts_list1 = get_ts_list(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"))
    if ts_list1 is None:
        # logging.info("Failed: M3U8 new playlist check failed.")
        print("Failed: M3U8 new playlist check failed.")
        return False,None

    # print(ts_list)
    # print(ts_list1)

    # 删除原始切片
    os.remove(os.path.join(m3u8folder_path, m3u8_name).replace("\\", "/"))
    for ts_file in ts_list:
        ts_file_path = os.path.join(m3u8folder_path, ts_file).replace("\\", "/")
        os.remove(ts_file_path)

    # print('视频上传并切片加密成功！')

    return True,ts_list1


#解密m3u8 并合并成原视频 xiaojuzi v2 20240102
def decrypt_m3u8(m3u8_path):

    try:

        # 检查M3U8列表
        ts_list = get_ts_list(os.path.join(m3u8_path, 'encrypted_slice.m3u8').replace("\\", "/"))
        if ts_list is None:
            print("Failed: M3U8 playlist check failed.")
            return False

        # print(ts_list)

        with open('./keyinfo.txt', 'r') as f:
            keyinfo = f.read().splitlines()

        iv = keyinfo[2]

        encryption_key = keyinfo[0]

        with open(encryption_key, "rb") as key_file:
            encryption_key1 = key_file.read().hex()

        # print(encryption_key1)

        decrypted_folder = os.path.join(m3u8_path, 'decrypted_folder')
        if not os.path.exists(decrypted_folder):
            os.makedirs(decrypted_folder)
            # 设置文件夹权限为管理员权限
            # os.chmod(decrypted_folder, 0o700)


        # 解密每个切片
        for i, encrypted_slice in enumerate(ts_list):

            encrypted_slice_path = os.path.join(m3u8_path, encrypted_slice).replace("\\", "/")
            # print(encrypted_slice_path)
            decrypted_slice_path = os.path.join(decrypted_folder, f'decrypted_slice_{i:05d}.ts').replace("\\", "/")
            # print(decrypted_slice_path)

            # 解密切片
            command = [
                'openssl', 'aes-128-cbc',
                '-d',
                '-in', encrypted_slice_path,
                '-out', decrypted_slice_path,
                '-nosalt',
                '-iv', iv,
                '-K', encryption_key1
            ]


            subprocess.run(command, check=True)

        # 合并解密后的切片为完整视频
        # 构建 FFmpeg 命令来合并解密后的切片
        concatenation_list = '|'.join(
            [f'{decrypted_folder}/decrypted_slice_{i:05d}.ts'.replace("\\", "/") for i in range(len(ts_list))])

        # print(concatenation_list)

        output_path = m3u8_path +'/decrypt_video.mp4'

        ffmpeg_command = [
            ffmpeg_path,
            '-i', f'concat:{concatenation_list}',
            '-c', 'copy',
            output_path
        ]

        # 执行 FFmpeg 命令
        subprocess.run(ffmpeg_command, check=True)

        # 删除解密后的原始切片
        shutil.rmtree(decrypted_folder.replace("\\", "/"))

    except Exception as e:
        print(e)



if __name__ == '__main__':
    ffmpeg_path = 'D:\\桌面\\ffmpeg\\ffmpeg.exe'
    ffprobe_path = 'D:\\桌面\\ffmpeg\\ffprobe.exe'
    ffplay_path = 'D:\\桌面\\ffmpeg\\ffplay.exe'
    video_path = './1.mp4'
    output_path = './temp_video_output'
    target = './temp_video_output/slice.m3u8'
    generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path)

    decrypt_m3u8(output_path)

    # print(generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path))
    # result = get_video_duration(ffprobe_path,video_path)
    # print(result)

    # result1 =check_video_time(ffprobe_path, video_path, target)
    # print(result1)
    # list = get_ts_list(output_path)
    # print(list)