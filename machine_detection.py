# LSD直线检测算法识别钻头坐标
import cv2
import numpy as np
from adjust_camera import adjust_camera
from sympy import *
global xmin, xmax, ymin, ymax, zp

def drill_detect(img):
    global xmin, xmax, ymin, ymax, zp
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edge_img = cv2.Canny(gray_img, 100, 100)
    edge_img = cv2.GaussianBlur(edge_img, (5, 5), 0)
    edge_img = cv2.morphologyEx(edge_img, cv2.MORPH_OPEN, (5, 5))
    # Create default parametrization LSD
    lsd = cv2.createLineSegmentDetector(0)
    # Detect lines in the image
    lines_x = lsd.detect(edge_img)[0]  # Position 0 of the returned tuple are the detected lines
    px = []
    if lines_x is not None:
        for line_x in lines_x:
            x1 = line_x[0][0]
            y1 = line_x[0][1]
            x2 = line_x[0][2]
            y2 = line_x[0][3]
            # 大车纵向直线识别判据：直线倾角大于80°且直线长度大于0.4倍的图像宽度
            if abs((y2 - y1)) / sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) > sin(80 * np.pi / 180) and abs(y2 - y1) > \
                    gray_img.shape[0] * 0.4:
                px.append(x1)
                px.append(x2)
                # print("大车纵向支架起点终点坐标：", x1, y1, x2, y2)
    else:
        return img, None, None, None
    if len(px) != 0:
        xmin = min(px)
        xmax = max(px)
        # print("xmin：", xmin, "  xmax：", xmax)
        # 将检测区域缩小至大车两条纵向直线之间
        roi_img = np.zeros([gray_img.shape[0], gray_img.shape[1]], np.uint8)
        # 裁取四周多余背景
        roi_img[int(gray_img.shape[0] * 0.4):int(gray_img.shape[0] * 0.9), int(xmin):int(xmax)] = 1
        # ndarray多维数组对应元素作乘法运算
        roi_img = np.multiply(roi_img, edge_img)
        # 在自定义目标区域中作小车横向直线识别
        lines_y = lsd.detect(roi_img)[0]
        py = []
        if lines_y is not None:
            for line_y in lines_y:
                x1 = line_y[0][0]
                y1 = line_y[0][1]
                x2 = line_y[0][2]
                y2 = line_y[0][3]
                # 小车横向直线识别判据：直线倾角小于5°且直线长度大于0.1倍的大车纵向直线间距
                if abs((y2 - y1)) / sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) < sin(5 * np.pi / 180) and abs(x2 - x1) > (
                        xmax - xmin) * 0.1:
                    py.append(y1)
                    py.append(y2)
                    # print("小车横向支架起点终点坐标：", x1, y1, x2, y2)
            # print("ymin：", ymin, "  ymax：", ymax)
        else:
            return img, None, None, None
        if len(py) != 0:
            ymin = min(py)
            ymax = max(py)
            cv2.line(img, (xmin, ymin), (xmax, ymin), (255, 0, 0), 15)
            cv2.line(img, (xmin, ymax), (xmax, ymax), (255, 0, 0), 15)
            cv2.line(img, (xmin, gray_img.shape[0]), (xmin, 0), (0, 0, 255), 15)
            cv2.line(img, (xmax, gray_img.shape[0]), (xmax, 0), (0, 0, 255), 15)
            zp = (0.5*(xmin + xmax), 0.5*(ymin + ymax))  # 钻头像素坐标
            zp_circle = (int(0.5*(xmin + xmax)), int(0.5*(ymin + ymax)))
            cv2.circle(img, zp_circle, 8, (0, 255, 0), 8)
            return img, zp, (xmax-xmin), (ymax-ymin)
        else:
            return img, None, None, None
    else:
        return img, None, None, None

if __name__ == "__main__":
    """img = cv2.imread("machine.jpg")
    result, zp, pls, pws = drill_detect(img)
    cv2.imwrite("LSD.jpg", result)
    print(f"钻头像素坐标：{zp}")"""
    cv2.namedWindow("sample_service", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("sample_service", 1920, 1080)
    rtsp = "rtsp://admin:admin@192.168.1.167:554/h264/ch1/main/av_stream"
    capture = cv2.VideoCapture(rtsp)
    while True:
        if capture.isOpened() is False:
            print("错误：相机初始化失败")
        ret, frame = capture.read()
        if ret is not True:
            print("错误：相机连接失败")
            break
        frame = adjust_camera(frame)
        result_z, zp, pls, pws = drill_detect(frame)
        cv2.imshow("carriage_detect", result_z)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break

