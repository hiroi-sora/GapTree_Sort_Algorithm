# 测试代码

import os
import json
import time
from pathlib import Path

from gap_tree import GapTree  # gap_tree.py

# 测试图片
# test_image = "test/1.png"  # 单栏布局，含有表格
# test_image = "test/2.png"  # 双栏布局，含有跨列的表格、图片
# test_image = "test/3.png"  # 双栏布局，含有大量列内图片、表格
# test_image = "test/4.png"  # 四栏布局（两页拼接），含有跨列标题
test_image = "test/5.png"  # 三栏布局，栏宽度差异大
# test_image = "test/6.png"

# 如果使用自己的图片，需要将OCR引擎【RapidOCR_json】放在本目录下。
# https://github.com/hiroi-sora/RapidOCR-json
# 也可以使用另外的任何OCR方式，或者从PDF中提取的文本。
# 要求：每个参与排序的元素块，都必须提供矩形包围盒的左上角和右下角坐标。

# ======================= 测试：获取文本块 =====================


def get_ocr_cache(image_path):  # 加载OCR缓存json文件
    absolute_path = os.path.abspath(image_path)
    # 尝试查找与图片同名的OCR结果缓存文件。
    json_path = Path(absolute_path).with_suffix(".json")
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            json_data = file.read()
        input_dict = json.loads(json_data)
        if input_dict["code"] == 100:
            return input_dict["data"]
    except Exception:
        pass
    return None


def get_rapidocr_json(image_path):
    # 调用 RapidOCR-json 引擎。下载：
    # https://github.com/hiroi-sora/RapidOCR-json
    try:
        from rapidocr import Rapid_pipe

        ocr = Rapid_pipe("RapidOCR_json/RapidOCR-json.exe", {"maxSideLen": 4096})
        absolute_path = os.path.abspath(image_path)
        result = ocr.run(absolute_path)
        if "code" in result and result["code"] == 100:
            json_path = Path(absolute_path).with_suffix(".json")
            print(f"OCR成功，获取{len(result['data'])}个文本块。")
            print(f"写入缓存：{json_path}")
            with open(json_path, "w", encoding="utf-8") as file:
                file.write(json.dumps(result))
            return result["data"]
    except Exception:
        pass
    return None


text_blocks = get_ocr_cache(test_image)
if not text_blocks:
    print(f"未获取缓存，尝试重新进行OCR。")
    text_blocks = get_rapidocr_json(test_image)
    if not text_blocks:
        print(f"RapidOCR-json 调用失败。")
        exit()

# ======================= 调用间隙树算法进行排序 =====================

t1 = time.time()


def tb_bbox(tb):  # 从文本块对象中，提取左上角、右下角坐标元组
    b = tb["box"]
    return (b[0][0], b[0][1], b[2][0], b[2][1])


gtree = GapTree()
sorted_text_blocks = gtree.sort(text_blocks, tb_bbox)  # 输入文本块，进行排序

t2 = time.time()
print(f"排序完毕。共{len(text_blocks)}个文本块，耗时{(t2-t1):.{6}f}s")

# ======================= 测试：结果可视化 =====================

try:
    from visualize import visualize
except Exception:
    print("无法加载结果可视化模块")
    exit()

# 原始OCR预览图
pil_origin = visualize(text_blocks, test_image).get(isOrder=True)
# 排序后的预览图
pil_sorted = visualize(sorted_text_blocks, test_image).get(isOrder=True)
# 左右拼接 1
pil_show_1 = visualize.createContrast(pil_origin, pil_sorted)

# 竖切线 预览图
cut_tbs = []
for c in gtree.current_cuts:
    x0 = c[0]
    x1 = c[1]
    y0 = gtree.current_rows[c[2]][0][0][1]
    y1 = gtree.current_rows[c[3]][0][0][3]
    cut_tbs.append({"box": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "text": ""})
pil_cuts = visualize(cut_tbs, test_image).get(isOrder=True)
# 树节点 预览图
node_tbs = []
for node in gtree.current_nodes:
    if not node["units"]:
        continue  # 跳过没有块的根节点
    x0 = node["x_left"]
    x1 = node["x_right"]
    y0 = gtree.current_rows[node["r_top"]][0][0][1]
    y1 = gtree.current_rows[node["r_bottom"]][0][0][3]
    node_tbs.append({"box": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "text": ""})
pil_nodes = visualize(node_tbs, test_image).get(isOrder=True)
# 左右拼接 2
pil_show_2 = visualize.createContrast(pil_cuts, pil_nodes)

print("可视化展示")
pil_show = visualize.createContrast(pil_show_1, pil_show_2)
pil_show.show()
