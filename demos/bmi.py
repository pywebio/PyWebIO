"""
BMI指数计算
^^^^^^^^^^^

计算 `BMI指数 <https://en.wikipedia.org/wiki/Body_mass_index>`_ 的简单应用

:demo_host:`Demo地址 </?pywebio_api=bmi>`  `源码 <https://github.com/wang0618/PyWebIO/blob/master/demos/bmi.py>`_
"""
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *


def main():
    set_output_fixed_height(True)
    set_title("BMI Calculation")

    put_markdown("""计算 [`BMI指数`](https://baike.baidu.com/item/%E4%BD%93%E8%B4%A8%E6%8C%87%E6%95%B0/1455733) 的简单应用，源代码[链接](https://github.com/wang0618/PyWebIO/blob/master/demos/bmi.py)""", lstrip=True)

    info = input_group('请输入', [
        input("请输入你的身高(cm)", name="height", type=FLOAT),
        input("请输入你的体重(kg)", name="weight", type=FLOAT),
    ])

    BMI = info['weight'] / (info['height'] / 100) ** 2

    top_status = [(14.9, '极瘦'), (18.4, '偏瘦'),
                  (22.9, '正常'), (27.5, '过重'),
                  (40.0, '肥胖'), (float('inf'), '非常肥胖')]

    for top, status in top_status:
        if BMI <= top:
            put_markdown('你的 BMI 值: `%.1f`，身体状态：`%s`' % (BMI, status))
            break


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
