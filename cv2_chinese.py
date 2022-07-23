# opencv中文标注
from PIL import Image, ImageFont, ImageDraw
import cv2
import numpy as np

# 重定义支持输出中文的cv2.putText
def cv2_put_chinese(img, chinese, left_top, textColor):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # cv2转PIL
        draw = ImageDraw.Draw(img)
        font = "C:/Windows/Fonts/msyh.ttc"  # 微软雅黑
        textSize = int(0.04*img.size[1] + 0.5)  # 字体大小随图像大小变化
        fontStyle = ImageFont.truetype(font, textSize, encoding="utf-8")  # 字体格式
        label_size = draw.textsize(chinese, fontStyle)  # 字体像素大小
        print(label_size)
        left = left_top[0]
        top = left_top[1] - label_size[1] - 8
        draw.text(xy=(left, top), text=chinese, fill=textColor, font=fontStyle)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)  # PIL转cv2

if __name__ == "__main__":
    image = cv2.imread("carriage_dark1.jpg")
    image = cv2_put_chinese(image, "珠海远光", (100, 200), "yellow")
    cv2.imwrite("chinese.jpg", image)
