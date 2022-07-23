# 四点式定框操作(按顺时针或逆时针方向依次定点)
import cv2
import datetime

global img, i, j, rect_point
i = 0
show_img = [0]*4
rect_point = [0]*4  # 矩形车框四个顶点坐标
back_point = [0]*4
winname = "draw_rect"

def draw_on_mouse(event, x, y, flags, param):
    global img, i, j, rect_point, back_point
    if event == cv2.EVENT_LBUTTONDOWN:  # 左键单击
        if i == 0:
            show_img[i] = img.copy()
        elif i > 0:
            show_img[i] = show_img[i - 1].copy()
        rect_point[i] = (x, y)
        j = i  # j恒为定点操作后当前状态下的i，便于b键连续回撤顶点操作
        cv2.circle(show_img[i], (x, y), 8, (255, 0, 0), -1)
        cv2.putText(show_img[i], f"P{i+1}", (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 0), 8)
        if i == 3:
            cv2.line(show_img[i], rect_point[0], rect_point[1], (0, 255, 0), 4)
            cv2.line(show_img[i], rect_point[0], rect_point[3], (0, 255, 0), 4)
            cv2.line(show_img[i], rect_point[1], rect_point[2], (0, 255, 0), 4)
            cv2.line(show_img[i], rect_point[2], rect_point[3], (0, 255, 0), 4)
        cv2.imshow(winname, show_img[i])
        print(f"车框顶点{i+1}坐标为：{rect_point[i]}")
        i += 1
        if i > 3:
            date = datetime.datetime.now().strftime('%Y:%m:%d')
            realtime = date + " " + datetime.datetime.now().strftime('%H:%M:%S.%f')[0:12]
            print(f"{realtime}  车框顶点坐标为：{rect_point}")
            i = 0
            back_point = rect_point  # 备份四个顶点坐标
            rect_point = [0]*4


def draw_rect(frame):
    global img, rect_point, back_point, i, j
    # img = cv2.imread('test_images/drill_bg.jpg')
    img = frame.copy()
    # cv2.WINDOW_NORMAL和0是一样的，设置成normal之后，拖动鼠标是可以改变窗口的大小的，不设置是改变不了窗口的大小的
    cv2.namedWindow(winname, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(winname, img.shape[1], img.shape[0])
    cv2.setMouseCallback(winname, draw_on_mouse)
    cv2.imshow(winname, img)
    while(True):
        k = cv2.waitKey(1) & 0xFF
        if k == ord('b'):  # b键删除顶点
            if j > 0:  # 删除车框顶点2、3、4
                rect_point[j] = 0
                cv2.imshow(winname, show_img[j-1])
                print(f"删除车框顶点{j+1}")
                j -= 1
                if i > 0:
                    i -= 1
                if i == 0:  # 定位车框顶点4后i=0
                    rect_point = back_point
                    i = 3
            elif j == 0 and i != 0:  # 删除车框顶点1
                rect_point = [0]*4
                cv2.imshow(winname, img)
                print(f"删除车框顶点{j+1}")
                i = 0
            elif j == 0 and i == 0:
                print("没有车框顶点")
        elif k == ord('d'):  # d键删除车框
            cv2.imshow(winname, img)
            rect_point = [0]*4
            print("删除所有顶点")
            i = 0
        elif k == ord('e'):  # e键退出定框程序
            cv2.destroyWindow(winname)
            print("退出定框操作")
            exit()

if __name__ == '__main__':
    draw_rect(cv2.imread("carriage_bg.jpg"))

