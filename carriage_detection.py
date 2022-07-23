import cv2
from adjust_camera import adjust_camera
global init_gt, rows, cols

gray_rate = 0.34  # 二值化阈值占平均灰度比率
area_rate = 0.015  # 矩形车框面积占单帧面积比率
area_sThre = area_rate * 1920 * 1080  # 车框面积阈值

# 帧差法识别矩形车框：背景帧、前景帧、采样区域数量、采样点编号、采样机初始位置
def carriage_detect(pre_img, cur_img, region_nums, sample_nums, init_position):
    global init_gt, rows, cols
    raw_img = cur_img.copy()
    previous_img = cv2.cvtColor(pre_img, cv2.COLOR_BGR2GRAY)
    sThre_p = gray_rate * cv2.mean(previous_img)[0]
    ret_p, previous_img = cv2.threshold(previous_img, sThre_p, 255, cv2.THRESH_BINARY_INV)
    current_img = cv2.cvtColor(cur_img, cv2.COLOR_BGR2GRAY)
    sThre_c = gray_rate * cv2.mean(current_img)[0]
    ret_c, current_img = cv2.threshold(current_img, sThre_c, 255, cv2.THRESH_BINARY_INV)
    diff_img = cv2.absdiff(current_img, previous_img)
    diff_img = cv2.GaussianBlur(diff_img, (5, 5), 0)
    # 按位与提取前景掩模
    gray_img = cv2.bitwise_and(diff_img, diff_img, mask=current_img)
    gray_img = cv2.morphologyEx(gray_img, cv2.MORPH_CLOSE, (3, 3))
    gray_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
    edge_img = cv2.Canny(gray_img, 255, 255)
    edge_img = cv2.GaussianBlur(edge_img, (5, 5), 0)
    # RETR_EXTERNAL—只给出最外层轮廓而非所有轮廓的层析结构，减少counters遍历次数
    rect_img, contours, hierarchy = cv2.findContours(edge_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 单帧图像中轮廓数量不为零
    if len(contours) > 0:
        contour_area = []
        for contour in contours:
            contour_area.append(cv2.contourArea(contour))
        area_max = max(contour_area)
        # 车框面积判据：排除行人等非运煤车移动物体
        if area_max > area_sThre:
            rect = contours[contour_area.index(area_max)]
            x, y, w, h = cv2.boundingRect(rect)
            result_img = cv2.rectangle(cur_img, (x, y), (x + w, y + h), (255, 0, 0), 3)
            if region_nums is not None:  # 还未接收到采样区域要求
                if init_position == 0:
                    init_gt = (x, (y + h))  # 钻头原点在车厢左下角
                elif init_position == 1:
                    init_gt = ((x + w), (y + h))  # 钻头原点在车厢右下角
                result_img = cv2.circle(result_img, init_gt, 8, (0, 255, 0), 6)
                if region_nums == 0:  # 采样区域数量为18(3行6列)
                    rows = 3
                    cols = 6
                elif region_nums == 1:  # 采样区域数量为9(3行3列)
                    rows = 3
                    cols = 3
                # 分割车框随机选取采样点
                for i in range(0, rows-1, 1):
                    result_img = cv2.line(result_img, (int(x), int(y + (i + 1) * h / rows)),
                                          (int(x + w), int(y + (i + 1) * h / rows)), (0, 0, 255), 3)
                for i in range(0, cols-1, 1):
                    result_img = cv2.line(result_img, (int(x + (i + 1) * w / cols), int(y)),
                                          (int(x + (i + 1) * w / cols), int(y + h)), (0, 0, 255), 3)
                # 标注采样点编号
                for i in range(0, cols, 1):
                    for j in range(0, rows, 1):
                        if i * 3 + j + 1 < 10:
                            if i * 3 + j + 1 in sample_nums:
                                result_img = cv2.putText(result_img, str(i * 3 + j + 1),
                                                         (int(x + i * w / cols + 10), int(y + j * h / rows + 20)),
                                                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4)
                            else:
                                result_img = cv2.putText(result_img, str(i * 3 + j + 1),
                                                         (int(x + i * w / cols + 10), int(y + j * h / rows + 20)),
                                                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 4)
                        else:
                            if i * 3 + j + 1 in sample_nums:
                                result_img = cv2.putText(result_img, str(i * 3 + j + 1),
                                                         (int(x + i * w / cols + 4), int(y + j * h / rows + 20)),
                                                         cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 4)
                            else:
                                result_img = cv2.putText(result_img, str(i * 3 + j + 1),
                                                         (int(x + i * w / cols + 4), int(y + j * h / rows + 20)),
                                                         cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 4)
            return result_img, area_max, init_gt, (x, y, w, h)
        else:
            return raw_img, 0, None, None
    if len(contours) == 0:
        return raw_img, 0, None, None

if __name__ == "__main__":
    img = cv2.imread("carriage_light.jpg")
    bg = cv2.imread("carriage_bg.jpg")
    result, max_area, init_gt, rect = carriage_detect(bg, img, None, None, None)
    cv2.imwrite("cp.jpg", result)
    """cv2.namedWindow("sample_service", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("sample_service", 1920, 1080)
    rtsp = "rtsp://admin:admin@192.168.1.167:554/h264/ch1/main/av_stream"
    capture = cv2.VideoCapture(rtsp)
    ret, bg = capture.read()  # 将首帧设置为运煤车停车后的背景图
    bg = adjust_camera(bg)
    # cv2.imwrite("background.jpg", bg)
    while True:
        if capture.isOpened() is False:
            print("错误：相机初始化失败")
        ret, frame = capture.read()
        if ret is not True:
            print("错误：相机连接失败")
            break
        frame = adjust_camera(frame)
        result, max_area, init_gt, rect = carriage_detect(cv2.imread('background.jpg'), frame, 0, [1, 5, 9], 0)
        cv2.imshow("carriage_detect", result)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break"""
