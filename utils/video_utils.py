import json
import logging
import multiprocessing
import os
import re
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
        # '-allowed_extensions','ALL'
        '-show_entries', 'format=duration',
        '-of', 'json',
        input_file
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout
        data = json.loads(output)
        # print(data)
        duration = float(data['format']['duration'])
        # print(duration)
        return duration
    except subprocess.CalledProcessError as e:
        logging.info('视频获取时长异常：'+str(e))
        # print(e)
        return 0


#根据dpi获取视频分辨率路径 xiaojuzi v2 20240126
def getVideoDpiPath(dpi):

    path = None
    if not dpi:
        return None

    if int(dpi) == 0:
        path = 'auto'
    elif int(dpi) == 1:
        path = '360p'
    elif int(dpi) == 2:
        path = '480p'
    elif int(dpi) == 3:
        path = '720p'
    elif int(dpi) == 4:
        path = '1080p'
    elif int(dpi) == 5:
        path = 'original'

    return path

#20240126 xiaojuzi v2 自定义切片参数 根据码率参数
def getVideoCommand(video_dpi,ffmpeg_path,video_path,cpu_count,keyinfo,m3u8folder_path,encrypted_m3u8_name):

    dpi_path = getVideoDpiPath(video_dpi)

    default_command = [
        ffmpeg_path,
        '-i', video_path,
        '-c:v', 'libx264',  # 对视频编码
        '-c:a', 'aac',  # 对音频编码
        '-s', '640x360',  # 输出视频分辨率
        '-pix_fmt', 'yuv420p',  # 输出视频像素格式
        '-b:a', '128k',  # 音频比特率
        '-b:v', '800k',  # 视频比特率
        '-r', '30',  # 输出视频帧率
        '-hls_key_info_file', keyinfo,  # 秘钥文件
        '-f', 'hls',  # 生成hls
        '-hls_time', '5',  # 切片变小
        '-hls_list_size', '0',  # 设置hls播放列表
        '-threads', str(cpu_count),  # 多处理器
        '-hls_playlist_type', 'vod',  # 点播
        '-force_key_frames', 'expr:gte(t,n_forced*1)',  # 添加强制关键帧参数
        '-hls_segment_filename', os.path.join(m3u8folder_path, f'encrypt_slice_%05d.ts').replace("\\", "/"),
        '-hls_flags', 'append_list',  # 追加到现有的播放列表
        os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/")
    ]

    if dpi_path == 'auto':
        command = [
            ffmpeg_path,
            '-i', video_path,
            '-c:v', 'libx264',  # 对视频编码
            '-c:a', 'aac',  # 对音频编码
            "-preset", "veryfast",  # 选择编码速度为非常快的预设
            "-tune", "zerolatency",  # 使用zerolatency调整参数，以减少编码延迟
            # "-g", "48",  # 关键帧间隔
            # "-sc_threshold", "0",  # 场景切换阈值 场景切换时立即生成新的关键帧
            # "-keyint_min", "48",  # 最小关键帧间隔 每个清晰度层级都有足够的关键帧
            "-b:v", "2000k", "-vf", "scale=1280:720",
            "-minrate:v", "1000k",
            "-maxrate:v", "4000k",  # 最大比特率 网络不够稳定就小点
            "-bufsize:v", "4000k",  # 码率缓冲区
            '-b:a', '128k',  # 音频比特率
            '-hls_key_info_file', keyinfo,  # 秘钥文件
            '-f', 'hls',  # 生成hls
            '-hls_time', '4',  # 切片变小
            '-hls_list_size', '0',  # 设置hls播放列表
            '-threads', str(cpu_count),  # 多处理器
            '-hls_playlist_type', 'vod',  # 点播
            '-hls_segment_filename', os.path.join(m3u8folder_path, f'encrypt_slice_%05d.ts').replace("\\", "/"),
            '-hls_flags', 'append_list',  # 追加到现有的播放列表
            # "-master_pl_name", os.path.join(m3u8folder_path, 'master.m3u8').replace("\\", "/"),
            # "-var_stream_map", "v:0,a:0 v:1,a:1 v:2,a:2 v:3,a:3",
            os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/")
        ]

        return command
    elif dpi_path == '360p':
        return default_command
    elif dpi_path == '480p':
        default_command[8] = '854x480'
        default_command[12] = '128k'
        default_command[14] = '1500k'
        return default_command
    elif dpi_path == '720p':
        default_command[8] = '1280x720'
        default_command[12] = '192k'
        default_command[14] = '2500k'
        return default_command
    elif dpi_path == '1080p':
        default_command[8] = '1920x1080'
        default_command[12] = '192k'
        default_command[14] = '5000k'
        return default_command
    elif dpi_path == 'original':
        default_command[4] = 'copy'
        default_command[6] = 'copy'
        default_command = [default_command[i] for i in range(len(default_command)) if i < 7 or i > 16]

        return default_command
    #默认不编码进行复制
    else:
        default_command[4] = 'copy'
        default_command[6] = 'copy'
        default_command = [default_command[i] for i in range(len(default_command)) if i < 7 or i > 16]

        return default_command

# 一次性加密切片 不会卡顿 20240116 xiaojuzi v2  缺点暂时无法校验时长是否一致
def test_generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path,video_dpi):

    ffmpeg_path = ffmpeg_path.replace('\\', '/')
    ffprobe_path = ffprobe_path.replace('\\', '/')
    video_path = video_path.replace('\\', '/')
    output_path = output_path.replace('\\', '/')

    # 初始化加密key 20240108 xiaojuzi v2
    keyinfo = init_hls_key(output_path,video_dpi)
    if not keyinfo:
        return False, None

    # print(keyinfo)

    if not os.path.exists(output_path):
        # 先删以前的在建立新的
        # shutil.rmtree(output_path)
        os.makedirs(output_path)

    # 获取服务器CPU数目
    cpu_count = multiprocessing.cpu_count()
    # print(cpu_count)

    m3u8folder_path = output_path
    encrypted_m3u8_name = 'encrypted_slice.m3u8'

    # 使用FFmpeg生成M3U8文件 获取对应分辨率参数

    command = getVideoCommand(video_dpi,ffmpeg_path,video_path,cpu_count,keyinfo,m3u8folder_path,encrypted_m3u8_name)

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.info('生成M3U8文件异常：' + str(e))
        # print(e)


    # 检查M3U8列表
    ts_list1 = get_ts_list(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"))
    if ts_list1 is None:
        logging.info("Failed: M3U8 new playlist check failed.")
        # print("Failed: M3U8 new playlist check failed.")
        return False,None


    # 打开加密索引文件进行信息混淆 20240108
    # 读取原始M3U8文件内容
    with open(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"), 'r') as f:
        original_content = f.read()
    # 替换敏感信息并保存到新的M3U8文件
    # 加密：METHOD=AES-128,URI="E:/drawbo/static/video/encrypt.key",IV=0x8c8f033870dc07570b8b74c6267f6564
    # modified_content = re.sub(r'METHOD=[^, \n]+', 'METHOD=ENCRYPTED', original_content)
    modified_content = re.sub(r'URI="[^"]+"', 'URI="SECRET"', original_content)
    # modified_content = re.sub(r'IV=[^, \n]+', 'IV=0x00000000000000000000000000000000', modified_content)

    with open(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"), 'w') as f:
        f.write(modified_content)

    # print('视频上传并切片加密成功！')
    logging.info("Success: Video upload and slice encryption succeeded.")

    return True,ts_list1


#将视频文件分片并加密 缺点在二个合并处稍微有一点点卡顿 拼接问题 待完善 xiaojuzi 20231230
def generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path):

    ffmpeg_path = ffmpeg_path.replace('\\','/')
    ffprobe_path = ffprobe_path.replace('\\','/')
    video_path = video_path.replace('\\','/')
    output_path = output_path.replace('\\','/')

    #初始化加密key 20240108 xiaojuzi v2
    keyinfo = init_hls_key(output_path)
    if not keyinfo:
        return False,None

    # print(keyinfo)

    if not os.path.exists(output_path):
        #先删以前的在建立新的
        # shutil.rmtree(output_path)
        os.makedirs(output_path)

    # 获取服务器CPU数目
    cpu_count = multiprocessing.cpu_count()
    # print(cpu_count)

    m3u8folder_path = output_path
    m3u8_name = 'slice.m3u8'
    encrypted_m3u8_name = 'encrypted_slice.m3u8'

    # 使用FFmpeg生成M3U8文件
    command = [
        ffmpeg_path,
        '-i', video_path,
        '-c:v', 'libx264',#对视频编码
        '-s', '1280x720',  # 输出视频分辨率
        '-pix_fmt', 'yuv420p',  # 输出视频像素格式
        '-b:a', '63k',  # 音频比特率
        '-b:v', '753k',  # 视频比特率
        '-r', '18',  # 输出视频帧率
        # '-c:v', 'copy',  # 对视频编码
        # '-c:a', 'copy',#对音频复制
        # '-c', 'copy',
        '-f', 'hls',#生成hls
        '-hls_time', '10',
        '-hls_list_size', '0',#设置hls播放列表
        '-threads', str(cpu_count),#多处理器
        '-hls_playlist_type', 'vod',#点播
        '-force_key_frames', 'expr:gte(t,n_forced*1)',  # 添加强制关键帧参数
        # '-hls_key_info_file', 'keyinfo.txt',#秘钥文件
        '-hls_segment_filename', os.path.join(m3u8folder_path, 'slice_%05d.ts').replace("\\", "/"),#生成ts文件
        os.path.join(m3u8folder_path, m3u8_name).replace("\\", "/")
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.info('生成M3U8文件异常：'+str(e))
        # print(e)

    # 检查视频时长
    check_time = check_video_time(ffprobe_path,video_path, os.path.join(m3u8folder_path, m3u8_name))
    if not check_time:
        logging.info("Failed: Video duration check failed.")
        # print("Failed: Video duration check failed.")
        return False,None

    # print("Success: Video duration check passed.")

    # 检查M3U8列表
    ts_list = get_ts_list(os.path.join(m3u8folder_path, m3u8_name))

    if ts_list is None:
        logging.info("Failed: M3U8 playlist check failed.")
        # print("Failed: M3U8 playlist check failed.")
        return False,None
    # print(ts_list)

    #对上传正确的视频进行加密
    for ts_file in ts_list:
        ts_file_path = os.path.join(m3u8folder_path, ts_file).replace("\\", "/")
        # temp = ts_file.split('.')[0]
        ts_duration = get_video_duration(ffprobe_path,ts_file_path)
        command = [
            ffmpeg_path,
            '-i', ts_file_path,
            # '-c:v', 'libx264',  # 对视频编码
            # '-c:v', 'copy',  # 对视频编码
            # '-c:a', 'copy',  # 对音频复制
            # '-i', video_path,
            '-c:v', 'libx264',#对视频编码
            '-s', '1280x720',  # 输出视频分辨率
            '-pix_fmt', 'yuv420p',  # 输出视频像素格式
            '-b:a', '63k',  # 音频比特率
            '-b:v', '753k',  # 视频比特率
            '-r', '18',  # 输出视频帧率
            # '-c', 'copy',
            # '-hls_key_info_file', 'keyinfo.txt',  # 秘钥文件
            '-hls_key_info_file', keyinfo,  # 秘钥文件
            '-f', 'hls',  # 生成hls
            '-hls_time', str(ts_duration),
            # '-hls_time', '10',
            '-hls_list_size', '0',  # 设置hls播放列表
            '-threads', str(cpu_count),  # 多处理器
            '-hls_playlist_type', 'vod',  # 点播
            '-force_key_frames', 'expr:gte(t,n_forced*1)',  # 添加强制关键帧参数
            '-hls_segment_filename', os.path.join(m3u8folder_path, f'encrypt_slice_%05d.ts').replace("\\", "/"),
            '-hls_flags', 'append_list',  # 追加到现有的播放列表
            os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/")
        ]
        try:
            subprocess.run(command)

        except subprocess.CalledProcessError as e:
            logging.info('视频分片加密异常：'+str(e))
            # print(e)

    # 检查M3U8列表
    ts_list1 = get_ts_list(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"))
    if ts_list1 is None:
        logging.info("Failed: M3U8 new playlist check failed.")
        # print("Failed: M3U8 new playlist check failed.")
        return False,None

    # print(ts_list)
    # print(ts_list1)

    # 删除原始切片
    os.remove(os.path.join(m3u8folder_path, m3u8_name).replace("\\", "/"))
    for ts_file in ts_list:
        ts_file_path = os.path.join(m3u8folder_path, ts_file).replace("\\", "/")
        os.remove(ts_file_path)

    #打开加密索引文件进行信息混淆 20240108
    # 读取原始M3U8文件内容
    with open(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"), 'r') as f:
        original_content = f.read()
    # 替换敏感信息并保存到新的M3U8文件
    #加密：METHOD=AES-128,URI="E:/drawbo/static/video/encrypt.key",IV=0x8c8f033870dc07570b8b74c6267f6564
    # modified_content = re.sub(r'METHOD=[^, \n]+', 'METHOD=ENCRYPTED', original_content)
    modified_content = re.sub(r'URI="[^"]+"', 'URI="SECRET"', original_content)
    # modified_content = re.sub(r'IV=[^, \n]+', 'IV=0x00000000000000000000000000000000', modified_content)

    with open(os.path.join(m3u8folder_path, encrypted_m3u8_name).replace("\\", "/"), 'w') as f:
        f.write(modified_content)

    # print('视频上传并切片加密成功！')
    logging.info("Success: Video upload and slice encryption succeeded.")

    return True,ts_list1

#初始化视频hls切片密钥 xiaojuzi 20240105
def init_hls_key(output_path,video_dpi):

    dpi_path = getVideoDpiPath(video_dpi)

    temp = output_path.split('/')[-2]
    # print(temp)

    key_path = os.path.dirname(os.path.dirname(os.path.dirname(output_path))) + f'/{temp}/{dpi_path}'
    # print(key_path)

    keyinfo = os.path.join(key_path, 'keyinfo.txt').replace("\\", "/")
    # print(keyinfo)
    # if os.path.isfile(keyinfo):
    #     return keyinfo
    # else:
    if not os.path.exists(key_path):
        os.makedirs(key_path)

    #更换逻辑 上传一次替换一次 加密算法 20240108
    key_file_path = os.path.join(key_path, 'encrypt.key').replace("\\", "/")
    try:
        command = f"openssl rand 16 > {key_file_path}"
        subprocess.run(command, shell=True)

        iv_output = subprocess.check_output(['openssl', 'rand', '-hex', '16'])
        # print(iv_output)
        iv = iv_output.decode().strip()
        # print(iv)

        with open(keyinfo, 'w') as f:
            f.write(key_file_path + '\n')
            f.write(key_file_path + '\n')
            f.write(iv + '\n')

        return keyinfo
    except Exception as e:
        logging.info('初始化生成密钥异常：'+str(e))
        return None



#解密m3u8 并合并成原视频 xiaojuzi v2 20240102
def decrypt_m3u8(m3u8_path,ffmpeg_path,keyinfo):

    try:

        # 检查M3U8列表
        ts_list = get_ts_list(os.path.join(m3u8_path, 'encrypted_slice.m3u8').replace("\\", "/"))
        if ts_list is None:
            logging.info("Failed: M3U8 playlist check failed.")
            # print("Failed: M3U8 playlist check failed.")
            return False

        # print(ts_list)

        with open(keyinfo, 'r') as f:
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
    output_path = 'E:\\drawbo_v2\\static\\video\\7\\6\\76824e4a0bdc63960f1affa262cc2685\\original'
    # target = './temp_video_output/slice.m3u8'
    # target1 = './temp_video_output/encrypted_slice.m3u8'
    # generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path)
    # keyinfo = 'E:\\temp_video_output\\keyinfo.txt'
    # decrypt_m3u8(output_path,ffmpeg_path,keyinfo)
    #dpi  :0 auto 1 360P  2 480p 3 720p 4 1080p 5 original
    test_generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path,5)
    # check_time = check_video_time(ffprobe_path, video_path,target1)
    # print(check_time)
    # result =get_encrypted_video_duration(ffprobe_path,target1)
    # print(result)
    # print(generate_m3u8(ffmpeg_path,ffprobe_path,video_path,output_path))
    # result = get_video_duration(ffprobe_path,video_path)
    # print(result)

    # result1 =check_video_time(ffprobe_path, video_path, target)
    # print(result1)
    # list = get_ts_list(output_path)
    # print(list)