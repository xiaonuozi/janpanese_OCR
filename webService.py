# C:\Users\14154\Downloads\DangoTranslator_4.5.8\DangoTranslator\app\config
# Image
from flask import Flask, request, jsonify
import argparse
import json
from paddleocr import PaddleOCR, draw_ocr
import uuid

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

# 失败的返回
def jsonFail(message):
    post_data = {
        "Code": -1,
        "Message": str(message),
        "RequestId": str(uuid.uuid4())
    }
    return jsonify(post_data)


# 成功的返回
def jsonSuccess(data):
    post_data = {
        "Code": 0,
        "Message": "Success",
        "RequestId": str(uuid.uuid4()),
        "Data": data
    }
    return jsonify(post_data)

def ocrResultSort(ocr_result):
    ocr_result.sort(key=lambda x: x[0][0][1])

    # 二次根据纵坐标数值分组（分行）
    all_group = []
    new_group = []
    flag = ocr_result[0][0][0][1]
    pram = max([int((i[0][3][1] - i[0][0][1]) / 2) for i in ocr_result])

    for sn, i in enumerate(ocr_result):
        if abs(flag - i[0][0][1]) <= pram:
            new_group.append(i)
        else:
            all_group.append(new_group)
            flag = i[0][0][1]
            new_group = [i]
    all_group.append(new_group)

    # 单行内部按左上点横坐标排序
    all_group = [sorted(i, key=lambda x: x[0][0][0]) for i in all_group]
    # 去除分组，归一为大列表
    all_group = [ii for i in all_group for ii in i]
    # 列表输出为排序后txt
    all_group = [ii for ii in all_group]

    return all_group

# ocr解析
def ocrProcess(imgPath, language):
    ocr = PaddleOCR(use_angle_cls=True, lang="japan")
    result = ocr.ocr(imgPath, cls=True)
    try:
        result = ocrResultSort(result)
    except Exception:
        pass

    resMapList = []
    for i in result:
        for line in i:
            print(line[1][0]+ "   Score{}",float(line[1][1]))
            resMap = {
                "Coordinate": {
                    "UpperLeft": line[0][0],
                    "UpperRight": line[0][1],
                    "LowerRight": line[0][2],
                    "LowerLeft": line[0][3]
                },
                "Words": line[1][0],
                "Score": float(line[1][1])
            }
            resMapList.append(resMap)

    return resMapList

def handle_request():
    # 获取请求体中的 JSON 数据
    post_data = request.get_data()
    post_data = json.loads(post_data.decode("utf-8"))
  
    # 在这里对请求数据进行处理和操作
    res = ocrProcess(post_data["ImagePath"], post_data["Language"])
    return jsonSuccess(res)
    

if __name__ == '__main__':
    host = "127.0.0.1"
    port = 6666
    path = "/ocr/api"
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--host", type=str, default=host, help="监听的主机。默认：\"%s\"" % host)
    parser.add_argument("-p", "--port", type=int, default=port, help="监听的端口。默认：%d" % port)
    parser.add_argument("-P", "--path", type=str, default=path, help="监听的路径。默认：\"%s\"" % path)
    parser.add_argument('--help', action='help', help='打印帮助。')
    args = parser.parse_args()
    path = args.path
    app.add_url_rule(path, view_func=handle_request, methods=["POST", "HEAD"])
    app.run(host=host, port=port)