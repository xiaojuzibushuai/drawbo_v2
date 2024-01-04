import logging
import os

import oss2
from config import oss_access_key_id, oss_access_key_secret, oss_bucket_name, \
    oss_endpoint
from utils.error_code import SUCCESS, VIDEO_UPLOAD_FAILED

#xiaojuzi v2 20231228 阿里云oss上传

bucket = oss2.Bucket(oss2.Auth(oss_access_key_id, oss_access_key_secret), oss_endpoint, oss_bucket_name)

def upload_file(object_key, file):
    try:
        # 将文件流的位置移动到文件末尾 区别在于第一种是flask上传的文件是stream，第二种是普通上传的文件是file
        # file.stream.seek(0, os.SEEK_END)
        file.seek(0, os.SEEK_END)
        # 获取当前位置的偏移量，即文件的大小
        # file_size = file.stream.tell()
        file_size = file.tell()
        # print(file_size)

        #指针恢复
        # file.stream.seek(0)
        file.seek(0)
        # 判断文件大小是否大于100M
        if file_size > 100 * 1024 * 1024:
            # 使用分片上传
            resume_upload(object_key,file)
            return SUCCESS
        else:
            # 使用普通上传
            result = bucket.put_object(object_key, file)
            # logging.info(f'Uploaded {object_key} of size {file_size} bytes,result:{result.status}')
            print(f'Uploaded {object_key} of size {file_size} bytes,result:{result.status}')
            return SUCCESS

    except Exception as e:
        # print(e)
        logging.info(f'Error uploading {object_key}: {e}')
        return VIDEO_UPLOAD_FAILED


#分片上传 xiaojuzi v2 20231228
def multipart_upload(object_key, file, part_size=10 * 1024 * 1024):
    # 将文件流的位置移动到文件末尾
    # file.stream.seek(0, os.SEEK_END)
    file.seek(0, os.SEEK_END)
    # 获取当前位置的偏移量，即文件的大小
    # total_size = file.stream.tell()
    total_size = file.tell()
    # 指针恢复
    # file.stream.seek(0)
    file.seek(0)

    upload_id = None

    try:
        # 初始化分片上传
        upload_id = bucket.init_multipart_upload(object_key).upload_id

        # 计算分片数量
        part_count = (total_size + part_size - 1) // part_size

        # 开始分片上传
        parts = []
        for i in range(part_count):
            offset = i * part_size
            size = min(part_size, total_size - offset)
            # chunk = file.read(size)
            upload_part = bucket.upload_part(object_key, upload_id, i + 1, oss2.SizedFileAdapter(file, size))
            parts.append(oss2.models.PartInfo(i + 1, upload_part.etag,size = size,part_crc = upload_part.crc))

        # 完成分片上传
        bucket.complete_multipart_upload(object_key, upload_id, parts)

        # print(f'Successfully uploaded {object_key}')
        logging.info(f'Successfully uploaded {object_key}')
    except Exception as e:
        # print(e)
        logging.info(f'Error uploading {object_key}: {e}')
        if upload_id:
            # 如果出错，取消分片上传
            bucket.abort_multipart_upload(object_key, upload_id)
            # print(f'Upload of {object_key} aborted')
            logging.info(f'Upload of {object_key} aborted')

#断点续传 xiaojuzi v2 20231228
def resume_upload(object_key, file, part_size=10 * 1024 * 1024):
    # 检查对象是否存在，如果存在则获取已上传的分片信息
    if bucket.object_exists(object_key):
        try:
            parts = bucket.list_parts(object_key)

            # 计算已上传的分片数
            uploaded_parts = [part.part_number for part in parts]
            next_part_number = max(uploaded_parts) + 1 if uploaded_parts else 1

            # 从上次上传结束的地方继续上传
            upload_id = get_upload_id(bucket, object_key)
            file.seek((next_part_number - 1) * part_size)
            chunk = file.read(part_size)

            upload_part = bucket.upload_part(object_key, upload_id, next_part_number, chunk)
            # print(f'Uploaded part {next_part_number}: {upload_part.etag}')
            logging.info(f'Uploaded part {next_part_number}: {upload_part.etag}')
        except Exception as e:
            # print(e)
            logging.info(f'Error uploading part {next_part_number}: {e}')
    else:
        # 如果对象不存在，则直接执行分片上传
        multipart_upload(object_key, file)

#
def get_upload_id(object_key):
    # 查询已经初始化的分片上传任务
    upload_list = bucket.list_multipart_uploads(prefix=object_key)

    # 遍历分片上传任务，找到对应的upload_id
    for upload in upload_list:
        if upload.key == object_key:
            return upload.upload_id

    # 如果没有找到对应的upload_id，说明还没有初始化分片上传任务，需要重新执行初始化分片上传
    multipart_upload = bucket.init_multipart_upload(object_key)
    return multipart_upload.upload_id


if __name__ == '__main__':
    # 上传本地文件
    file_path = 'E:/drawbo/static/video/12345/12345.mp4'
    upload_file('test.txt', open(file_path, 'rb'))
