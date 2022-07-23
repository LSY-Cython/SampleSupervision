import cv2
import tkinter as tk
from tkinter import scrolledtext
import logging
from logging.handlers import RotatingFileHandler
import datetime
import threading
import queue
import time
import configparser
import modbus_tk.modbus_tcp as mt
import modbus_tk.defines as md
from adjust_camera import adjust_camera
from carriage_detection import carriage_detect, area_sThre
from drill_detection import drill_detect, check_region
from draw_rect import draw_rect
from cfg_gui import cfg_params
global log_text, logger, config, capture, master, drill_bg, result_s, rect_s, carriage_length, carriage_width, init_gt_s, region_nums
global stop_flag
que_img = queue.Queue(4)

# 日志打印方法
def show_info(message):
    global log_text, logger
    logger = get_logger()
    log_text.configure(state=tk.NORMAL)
    date = datetime.datetime.now().strftime('%Y:%m:%d')
    time = datetime.datetime.now().strftime('%H:%M:%S.%f')[0:12]
    realtime = date + " " + time  # 精确到毫秒级
    sep = "--------"
    textvar = sep + realtime + sep + "\n" + time + "  " + message + "\n"
    log_text.insert("end", textvar)
    log_text.insert("insert", "\n")
    log_text.configure(state=tk.DISABLED)
    logger.info(message)

# 日志清除方法
def log_clear():
    global log_text
    log_text.configure(state=tk.NORMAL)
    log_text.delete(0.0, tk.END)  # 清楚text中的内容，0.0为删除全部
    log_text.configure(state=tk.DISABLED)

# 开启采样监督多线程服务
def daemon_start():
    global logger, config
    config = configparser.ConfigParser()
    config.read('cfg.ini')
    show_info("信息：开启采样监督服务")
    que_img.queue.clear()  # 清空队列
    rtsp = config.get('configuration', 'rtsp')
    camera_thread = threading.Thread(target=camera_daemon, args=(rtsp, ))
    detect_thread = threading.Thread(target=detect_daemon)
    camera_thread.start()  # 相机线程
    time.sleep(1)
    detect_thread.start()  # 坐标识别线程

# 停止采样监督多线程服务
def daemon_stop():
    global stop_flag, logger
    que_img.queue.clear()
    stop_flag = True
    show_info("信息：停止采样监督服务")

# 配置后台日志
def get_logger():
    log_format = "%(asctime)s-%(name)s-%(levelname)s-%(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    logger = logging.getLogger("远光采样监督")
    handler = RotatingFileHandler(filename='logging.txt', mode='a', maxBytes=5*1024*1024, backupCount=5)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

# 摄像头线程，通过队列传递图像
def camera_daemon(rtsp):
    global capture
    capture = cv2.VideoCapture(rtsp)
    while True:
        if capture.isOpened() is False:
            show_info("错误：相机初始化失败")
            break
        ret, frame = capture.read()
        if ret is False:
            show_info("错误：相机连接失败")
            break
        frame = adjust_camera(frame)
        que_img.put(frame)  # 队列会阻塞

# 采样区域与钻头识别线程，通过标志位区分不同状态
def detect_daemon():
    global stop_flag, master, drill_bg, result_s, rect_s, carriage_length, carriage_width, init_gt_s, region_nums
    stop_flag = False
    # 读取通讯参数配置
    plc_ip = config.get('configuration', 'plc_ip')
    plc_port = config.get('configuration', 'plc_port')
    slave_id = config.get('configuration', 'slave_id')
    save_path = config.get('configuration', 'save_path')
    # modbus保持寄存器地址
    car_length = 1  # 车厢长度(mm)
    car_width = 2  # 车厢宽度(mm)
    region_num = 3  # 采样区域数量
    init_location = 4  # 钻头初始原点
    obj_region1 = 5  # 目标采样区域1
    obj_region2 = 6  # 目标采样区域2
    obj_region3 = 7  # 目标采样区域3
    drill_region = [8, 9, 10]  # 实际采样区域
    x = [11, 13, 15]  # 目标采样区域物理坐标X
    y = [12, 14, 16]  # 目标采样区域物理坐标Y
    # 监督流程状态标志
    car_flag, park_flag = False, False
    cp_state, zp_state, leave_state = False, False, False  # 三种循环场景标志位
    sample_flag = [False]*3  # 三次采样监督标志位
    i, j = 0, 0  # 停车判断延时计数
    zp = [(0, 0)]*2  # 存储连续两个钻头像素坐标
    k = 0  # 钻头坐标识别延时计数
    n = 0  # 采样监督次数
    cv2.namedWindow("sample_service", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("sample_service", 1920, 1080)
    try:  # 初始化PLC通讯
        master = mt.TcpMaster(host=plc_ip, port=plc_port)
        time.sleep(1)
        carriage_bg = cv2.imread("carriage_bg.jpg")  # 车框识别静态背景
        while True:
            if stop_flag is True:
                break
            try:
                if cp_state is False:  # 状态1：采样区域识别
                    # 连续读取两帧
                    if que_img.qsize() >= 2:
                        frame_0 = que_img.get()
                        frame_1 = que_img.get()
                        # 静态背景减除法判定相机视野中是否存在运煤车
                        result_s, max_area_s, init_gt_s, rect_s = carriage_detect(carriage_bg, frame_1, None, None, None)
                        if max_area_s < area_sThre:  # 无运煤车进入相机视野
                            cv2.imshow('sample_service', frame_1)
                        if max_area_s >= area_sThre:  # 当有运煤车进入相机视野时开启车框动态识别
                            if car_flag is False:
                                show_info("状态：有运煤车辆进入现场")
                                car_flag = True
                                leave_state = False
                            # 动态插帧法判定车辆运动状态
                            result_d, max_area_d, init_gt_d, rect_d = carriage_detect(frame_0, frame_1, None, None, None)
                            if max_area_d < area_sThre:
                                i += 1  # 延时大约100*2帧后连续两帧的前景之间仍无明显变化时判定为停车
                                if i == 100 and park_flag is False:
                                    show_info("信息：煤车辆已停车，请给定采样要求")
                                    park_flag = True
                                    i = 0
                                    carriage_length = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, car_length, 1)[0])
                                    carriage_width = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, car_width, 1)[0])
                                    region_nums = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, region_num, 1)[0])
                                    init_position = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, init_location, 1)[0])
                                    sample_num1 = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, obj_region1, 1)[0])
                                    sample_num2 = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, obj_region2, 1)[0])
                                    sample_num3 = int(master.execute(slave_id, md.READ_HOLDING_REGISTERS, obj_region3, 1)[0])
                                    sample_nums = [sample_num1, sample_num2, sample_num3]
                                    result_s, max_area_s, init_gt_s, rect_s = carriage_detect(carriage_bg, frame_1, region_nums, sample_nums, init_position)
                                    drill_bg = frame_1.copy()  # 截取停车现场作为钻头跟踪背景
                                    cp_state = True  # 完成采样点和原点坐标识别
                            cv2.imshow('sample_service', result_s)
                if cp_state is True and zp_state is False:  # 状态2：完成采样区域识别后再进入钻头跟踪
                    if que_img.qsize() >= 1:
                        frame = que_img.get()
                        drill_result, drill_gt = drill_detect(drill_bg, frame, result_s, rect_s)
                        if drill_gt is not None:
                            zp[0] = zp[1]
                            zp[1] = drill_gt
                            # 钻头垂直下落时在图像中的轨迹是一条直线，若钻头坐标在设定时间内基本不变，则此稳定点可判定为钻头坐标
                            if abs(zp[1][0] - zp[0][0]) < 10 and abs(zp[1][1] - zp[0][1] < 5):
                                k += 1
                            if k == 100:
                                sample_x = abs(init_gt_s[0]-drill_gt[0])*carriage_length/rect_s[2]
                                master.execute(slave_id, md.WRITE_SINGLE_REGISTER, x[n], int(sample_x))
                                sample_y = abs(init_gt_s[1]-drill_gt[1])*carriage_width/rect_s[3]
                                master.execute(slave_id, md.WRITE_SINGLE_REGISTER, y[n], int(sample_y))
                                sample_number = check_region(drill_gt, region_nums, rect_s)
                                master.execute(slave_id, md.WRITE_SINGLE_REGISTER, drill_region[n], sample_number)
                                k = 0
                                show_info(f"信息：完成第{n+1}次采样监督")
                                sample_flag[n] = True
                                n += 1
                            if n == 3:
                                n = 0
                                show_info(f"状态：三次采样监督已完成")
                        cv2.imshow('sample_service', drill_result)
                    if sample_flag == [True]*3:
                        zp_state = True  # 监督钻头完成三次采样
                        sample_flag = [False]*3
                if (cp_state and zp_state) is True and leave_state is False:  # 状态3：完成钻头监督后运煤车离场
                    # 连续读取两帧
                    if que_img.qsize() >= 2:
                        frame_0 = que_img.get()
                        frame_1 = que_img.get()
                        # 动态差帧法监测运煤车离场
                        result_d, max_area_d, init_gt_d, rect_d = carriage_detect(frame_0, frame_1, None, None, None)
                        if max_area_d > area_sThre and park_flag is True:  # 当连续两帧之前有明显变化时可判定为运煤车离开
                            show_info("状态：运煤车辆正在离场")
                            park_flag = False
                        else:
                            j += 1
                            if j == 100:
                                show_info("状态：运煤车辆已离开")
                                carriage_bg = frame_1.copy()  # 车辆离场后更新车框识别背景
                                cv2.imwrite("carriage_bg.jpg", carriage_bg)
                                leave_state = True
                                cp_state, zp_state, car_flag = False, False, False
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    capture.release()
                    break
            except Exception as modbus_err:
                show_info("错误：PLC通讯中断，退出监督服务")
                break
    except Exception as modbus_err:
        show_info("错误：PLC通讯连接失败")
    finally:
        show_info("状态：退出PLC通讯进程")
        master.close()
        del master

# 初始化服务界面
def init_gui():
    global log_text
    # 主界面
    root = tk.Tk()
    root.title("远光采样监督服务")
    root.geometry('640x460')
    # 功能按钮
    start_button = tk.Button(root, text="开启", width=8, command=daemon_start)
    start_button.place(x=200, y=30)
    stop_button = tk.Button(root, text="停止", width=8, command=daemon_stop)
    stop_button.place(x=280, y=30)
    clear_button = tk.Button(root, text="清空", width=8, command=log_clear)
    clear_button.place(x=360, y=30)
    set_button = tk.Button(root, text="配置", width=8, command=cfg_params)
    set_button.place(x=440, y=30)
    draw_button = tk.Button(root, text="定框", width=8, command=lambda: draw_rect(que_img.get()))
    draw_button.place(x=520, y=30)
    # 日志显示(滚动文本框)
    log_label = tk.Label(root, text="日志打印：")
    log_label.place(x=15, y=75)
    log_sy = tk.Scrollbar(root, orient=tk.VERTICAL)
    log_text = scrolledtext.ScrolledText(root, bg="white", width=86, height=26)
    log_text.place(x=16, y=105)
    log_text.configure(state=tk.DISABLED)
    root.mainloop()

if __name__ == "__main__":
    init_gui()
