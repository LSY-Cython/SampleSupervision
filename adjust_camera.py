# 相机畸变矫正
import cv2
import numpy as np

def adjust_camera(img):
    camera_params = np.load('camera_params.npz')
    mtx = camera_params["mtx"]
    dist = camera_params["dist"]
    h, w = img.shape[:2]
    newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
    mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
    dst = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
    x, y, w, h = roi
    dst = dst[y:y + h, x:x + w]
    return dst
