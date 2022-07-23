import cv2
import numpy as np
from sympy import *
area_rate = 0.0125  # 钻头在车框区域中的面积比率
global rows, cols

# 背景减除法识别钻头：停车背景、钻头前景、采样区域识别结果、矩形车框
def drill_detect(bg, img, carriage_img, car_rect):
    # 制作矩形车框掩模定位在采样区域内运动的钻头，并且要消除车框边缘对钻头面积阈值的影响
    x, y, w, h = int(car_rect[0]), int(car_rect[0]), int(car_rect[0]), int(car_rect[0])
    roi_img = np.zeros([img.shape[0], img.shape[1]], np.uint8)
    roi_img[y+20:y+h-20, x:x+w] = 255
    bg = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    retb, bg = cv2.threshold(bg, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # 大津法自动二值化
    reti, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    diff_img = cv2.absdiff(img, bg)
    diff_img = cv2.medianBlur(diff_img, 3)  # 中值滤波去除煤碳颗粒的噪声影响
    diff_img = cv2.morphologyEx(diff_img, cv2.MORPH_CLOSE, (5, 5))
    diff_img = cv2.bitwise_and(diff_img, diff_img, mask=roi_img)
    diff_img = cv2.Canny(diff_img, 255, 255)
    diff_img = cv2.GaussianBlur(diff_img, (5, 5), 0)
    rect_img, contours, hierarchy = cv2.findContours(diff_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        contour_area = []
        for contour in contours:
            contour_area.append(cv2.contourArea(contour))
        area_max = max(contour_area)
        if area_max > area_rate * w * h:
            cnt = contours[contour_area.index(area_max)]
            ellipse = cv2.fitEllipse(cnt)
            w = ellipse[1][1]  # 长轴长度
            angle = ellipse[2]  # 旋转角度(相对于直轴)
            zpx = ellipse[0][0] - w * sin(angle * np.pi / 180) / 2
            zpy = ellipse[0][1] + w * cos(angle * np.pi / 180) / 2
            result_img = cv2.ellipse(carriage_img, ellipse, (255, 0, 0), 2)
            result_img = cv2.circle(result_img, (int(zpx), int(zpy)), 8, (0, 0, 255), -1)
            return result_img, (zpx, zpy)
        else:
            return carriage_img, None
    else:
        return carriage_img, None

# 判断钻头的实际采样区域：钻头坐标、采样区域数量、矩形车框
def check_region(zp, region_nums, rect):
    global rows, cols
    if region_nums == 0:  # 采样区域数量为18(3行6列)
        rows = 3
        cols = 6
    elif region_nums == 0:  # 采样区域数量为9(3行3列)
        rows = 3
        cols = 3
    x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    i = (zp[0] - x) // (w / cols)
    j = (zp[1] - y) // (h / rows)
    num = 1 + 3 * i + j  # 实际采样区域编号
    return num
