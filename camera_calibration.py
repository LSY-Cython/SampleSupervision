# 棋盘法标定相机
import numpy as np
import cv2
import glob
global gray

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(10,7,0)
objp = np.zeros((10*7, 3), np.float32)
objp[:, :2] = np.mgrid[0:10, 0:7].T.reshape(-1, 2)
# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.
images = glob.glob('./chess_samples/*.jpg')
cv2.namedWindow("img", cv2.WINDOW_NORMAL)
cv2.resizeWindow("img", 1920, 1080)
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (10, 7), None)
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (10, 7), corners2, ret)
        cv2.imshow('img', img)
        # cv2.imwrite(f"chess_samples/{images.index(fname)+1}.jpg", img)
        cv2.waitKey(500)
cv2.destroyAllWindows()
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
dist[0][4] = 0
print("相机内参矩阵：", mtx)
print("五个畸变系数：", dist)
np.savez('camera_params', mtx=mtx, dist=dist)  # 保存数组到二进制文件中
print("旋转外参向量：", rvecs)
print("平移外参向量：", tvecs)
