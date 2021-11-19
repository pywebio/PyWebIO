from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import info as session_info


def t(eng, chinese):
    """return English or Chinese text according to the user's browser language"""
    return chinese if 'zh' in session_info.user_language else eng


def main():
    """BMI Calculation

    Simple application for calculating Body Mass Index.
    计算BMI指数的简单应用
    """

    put_markdown(t("""# Body Mass Index
    
    [Body mass index](https://en.wikipedia.org/wiki/Body_mass_index) (BMI) is a measure of body fat based on height and weight that applies to adult men and women. 
    
    BMI Categories:
    
    | Category             | BMI           |
    | -------------------- | ------------- |
    | Severely underweight | BMI<14.9      |
    | Underweight          | 14.9≤BMI<18.4 |
    | Normal               | 18.4≤BMI<22.9 |
    | Overweight           | 22.9≤BMI<27.5 |
    | Moderately obese     | 27.5≤BMI<40   |
    | Severely obese       | BMI≥40        |
    
    ## BMI calculation
    The source code of this application is [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/bmi.py)
    """, """# BMI指数

    [`BMI指数`](https://baike.baidu.com/item/%E4%BD%93%E8%B4%A8%E6%8C%87%E6%95%B0/1455733)（Body Mass Index，BMI），是用体重千克数除以身高米数的平方得出的数字，是国际上常用的衡量人体胖瘦程度以及是否健康的一个标准。
    
    成年人的BMI值处于以下阶段
    
    | 体形分类 | BMI值范围 |
    | ------ | -------- |
    | 极瘦    | BMI<14.9    |
    | 偏瘦    | 14.9≤BMI<18.4     |
    | 正常    | 18.4≤BMI<22.9     |
    | 过重    |  22.9≤BMI<27.5  |
    | 肥胖    |  27.5≤BMI<40  |
    | 非常肥胖 |     BMI≥40      |
    
    ## BMI指数计算器
    本程序的源代码[链接](https://github.com/wang0618/PyWebIO/blob/dev/demos/bmi.py)
    
    """))

    info = input_group(t('BMI calculation', '计算BMI：'), [
        input(t("Your Height(cm)", "请输入你的身高(cm)"), name="height", type=FLOAT),
        input(t("Your Weight(kg)", "请输入你的体重(kg)"), name="weight", type=FLOAT),
    ])

    BMI = info['weight'] / (info['height'] / 100) ** 2

    top_status = [(14.9, t('Severely underweight', '极瘦')), (18.4, t('Underweight', '偏瘦')),
                  (22.9, t('Normal', '正常')), (27.5, t('Overweight', '过重')),
                  (40.0, t('Moderately obese', '肥胖')), (float('inf'), t('Severely obese', '非常肥胖'))]

    for top, status in top_status:
        if BMI <= top:
            put_markdown(t('Your BMI: `%.1f`, Category: `%s`', '你的 BMI 值: `%.1f`，身体状态: `%s`') % (BMI, status))
            break


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
