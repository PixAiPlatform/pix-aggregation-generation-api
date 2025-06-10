# -*- coding: utf-8 -*-
import base64
import json

from PIL import Image
from io import BytesIO

import numpy as np
import requests
import fal_client


# 必要 初始化函数
# config - 由上层调度框架注入
# 首次会在进程启动时会执行一次，其他之后将不会再执行，可在此函数做对象初始化和模型加载
def Init(config):
    print("init success")


# 运行handle 所有请求都会经过此函数处理 最终也会由该函数返回给上层框架
# body - http request body 参数 框架透传
# extra - 上层框架注入 ex：traceid等
# 统一返回格式array:return [json.dumps({"ErrorCode": 20014, "ErrorMsg": "NOT_FOUND"}), 20014, "NOT_FOUND"]
def Process(body, extra):
    global result
    body_json = json.loads(body)
    parameter = body_json.get("parameter", {})
    if parameter["model"] == "flux-pro/kontext":
        result = flux_pro_async(body_json)
    media_info_list = []
    for result_data in result["images"]:
        media_info_list.append(transformImage(result_data["url"]))
    resp = [json.dumps({
        "parameter": {
            "version": "1.0.0",
            "rsp_media_type": "url"
        },
        "media_info_list": media_info_list
    }, cls=MyEncoder, indent=4), 0, ""]
    return resp


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


def flux_pro_async(body):
    parameter = body.get("parameter", {})
    media_info_list = body.get("media_info_list", [])
    result = fal_client.subscribe(
        "fal-ai/flux-pro/kontext",
        arguments={
            "prompt": parameter.get('prompt', ''),
            "guidance_scale": parameter.get('guidance_scale', '3.5'),
            "num_images": parameter.get('batch_size', 1),
            "aspect_ratio": parameter.get('aspect_ratio', '1:1'),
            "image_url": media_info_list[0]['media_data'] if media_info_list else None,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    print(result)
    return result


def transformImage(input_data):
    # 判断输入是 URL 还是 Base64 字符串
    if input_data.startswith('http://') or input_data.startswith('https://'):
        # 处理 URL
        url_response = requests.get(input_data)
        if url_response.status_code == 200:
            image_data = url_response.content
        else:
            print("Failed to retrieve image from URL.")
            return None
    else:
        # 处理 Base64 数据
        try:
            # 尝试解码 Base64 数据
            image_data = base64.b64decode(input_data)
        except (TypeError, ValueError):
            print("Invalid Base64 string.")
            return None

    # 使用 PIL 打开图像
    with Image.open(BytesIO(image_data)) as img:
        # 获取图片的宽度和高度
        width, height = img.size

    size_in_bytes = len(image_data)

    # 检查大小和尺寸
    if size_in_bytes > (5 * 1024 * 1024) or width > 4096 or height > 4096:
        tools_url = "https://image-tools.airbrush.com/api/v1/image/thumbnail"
        resp = requests.post(url=tools_url, json={
            "inputImage": input_data,
            "inputImageDataType": "base64" if 'base64_str' in locals() else "url",
            "outputImageDataType": "base64",
            "width": 1024,
            "height": 1024
        }, verify=True)
        result_json = json.loads(resp.text)
        base64_str = result_json['data']['outputImage']
    else:
        # 直接使用原始 Base64 数据
        base64_str = base64.b64encode(image_data).decode('utf-8')

    # 上传 Base64 数据
    url = "http://open-flow.algorithm.svc.cluster.local/open/putbase64?api_key=EtRGxLI8ulQ43pGhuZfym9aYUD2PUbMP&type=1"
    resp = requests.post(url=url, data=base64_str, verify=True)
    result_json = json.loads(resp.text)

    # 获取最终的图像 URL
    image_url = result_json['key']
    return image_url


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        return json.JSONEncoder.default(self, obj)


# python run test
if __name__ == '__main__':
    json_data = '''{
    "parameter": {
        "rsp_media_type": "url",
        "prompt" : "Put a donut next to the flour",
        "model": "flux-pro/kontext"
     },
    "media_info_list": [
         {
            "media_data": "https://v3.fal.media/files/rabbit/rmgBxhwGYb2d3pl3x9sKf_output.png",
            "media_profiles": {
                "media_data_type": "url"
            }
        }
    ]
}'''
    Init(None)
    response = Process(json_data, "")
    print(response)
    pass
