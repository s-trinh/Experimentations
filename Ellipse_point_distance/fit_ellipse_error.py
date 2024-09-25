#!/usr/bin/env python3
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from timeit import default_timer as timer
from datetime import timedelta

def getEllipsePointsCV(ellipse):
    center, axes, angle = ellipse
    ellipse_points = cv.ellipse2Poly((int(center[0]), int(center[1])), (int(axes[0] // 2), int(axes[1] // 2)), int(angle), 0, 360, 1)

    return ellipse_points

# https://stackoverflow.com/a/46007540
# https://blog.chatfield.io/simple-method-for-distance-to-ellipse/
# https://github.com/0xfaded/ellipse_demo/blob/a420f76942092f06c822c45db5d5fedd10224bc9/ellipse_trig_free.py
def solveFast(semi_major, semi_minor, p):
    px = abs(p[0])
    py = abs(p[1])

    tx = 0.707
    ty = 0.707

    a = semi_major
    b = semi_minor

    for x in range(0, 3):
        x = a * tx
        y = b * ty

        ex = (a*a - b*b) * tx**3 / a
        ey = (b*b - a*a) * ty**3 / b

        rx = x - ex
        ry = y - ey

        qx = px - ex
        qy = py - ey

        r = np.hypot(rx, ry)
        q = np.hypot(qx, qy)

        tx = min(1, max(0, (qx * r / q + ex) / a))
        ty = min(1, max(0, (qy * r / q + ey) / b))
        t = np.hypot(tx, ty)
        tx /= t
        ty /= t

    return (np.copysign(a * tx, p[0]), np.copysign(b * ty, p[1]))

def getTransfo(theta, shift):
    T = np.eye(3)

    T[0,0] = np.cos(theta)
    T[0,1] = np.sin(theta)
    T[0,2] = -np.cos(theta)*shift[0] - np.sin(theta)*shift[1]
    T[1,0] = -np.sin(theta)
    T[1,1] = np.cos(theta)
    T[1,2] = np.sin(theta)*shift[0] - np.cos(theta)*shift[1]

    return T

def getEllipseFittingError(points, ellipse_params):
    semi_major = ellipse_params[1][0] / 2
    semi_minor = ellipse_params[1][1] / 2
    if semi_major < semi_minor:
        semi_minor, semi_major = semi_major, semi_minor

    align_T_ori = getTransfo(np.deg2rad(ellipse_params[2] if ellipse_params[1][0] > ellipse_params[1][1] else ellipse_params[2]+90), ellipse_params[0])

    dist_error = 0
    for pt in points:
        X_align = align_T_ori @ np.array([pt[0],pt[1],1])
        X_align /= X_align[2]
        closest_pt = solveFast(semi_major, semi_minor, (X_align[0], X_align[1]))
        dist_error += np.hypot(X_align[1]-closest_pt[1], X_align[0]-closest_pt[0])

    return dist_error / len(points) if len(points) > 0 else 1e9

def scaleApplyColormap(img_float):
    x1 = np.max(img_float)
    x0 = np.min(img_float)
    if x1 - x0 > 1e-3:
        a = 255 / (x1 - x0)
        b = -a * x0

        img = cv.convertScaleAbs(img_float, alpha=a, beta=b)
        return cv.applyColorMap(img, cv.COLORMAP_TURBO)

    return np.zeros(img_float.shape, dtype=np.uint8)

def getIntPts(pts):
    pts_int = np.empty((len(pts), 2), dtype=np.int32)
    for idx, pt in enumerate(pts):
        pts_int[idx,0] = pt[0]
        pts_int[idx,1] = pt[1]

    return pts_int

def drawEllipseDistanceMap(points, ellipse_params):
    bb_rect = cv.boundingRect(points)
    bb_rect_w = bb_rect[0] + bb_rect[2]
    bb_rect_h = bb_rect[1] + bb_rect[3]
    img = np.zeros((np.int32(bb_rect_h*1.5), np.int32(bb_rect_w*1.5), 3), dtype=np.uint8)

    semi_major = ellipse_params[1][0] / 2
    semi_minor = ellipse_params[1][1] / 2
    if semi_major < semi_minor:
        semi_minor, semi_major = semi_major, semi_minor

    dist_map = np.zeros(img.shape, dtype=np.float32)
    align_T_ori = getTransfo(np.deg2rad(ellipse_params[2] if ellipse_params[1][0] > ellipse_params[1][1] else ellipse_params[2]+90), ellipse_params[0])

    start = timer()
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            X_align = align_T_ori @ np.array([j,i,1])
            X_align /= X_align[2]

            closest_pt = solveFast(semi_major, semi_minor, (X_align[0], X_align[1]))
            dist_map[i,j] = np.hypot(X_align[1]-closest_pt[1], X_align[0]-closest_pt[0])
    end = timer()
    print(f"Computation time: {timedelta(seconds=end-start)}")

    dist_map_u8 = scaleApplyColormap(dist_map)
    ellipse_points_cv = getEllipsePointsCV(ellipse_params)
    cv.polylines(dist_map_u8, [getIntPts(ellipse_points_cv)], isClosed=False, color=(0,0,255), thickness=3)
    for circle in points:
        cv.circle(dist_map_u8, circle, radius=8, color=(255,0,0), thickness=2)

    return dist_map_u8

# https://github.com/opencv/opencv/issues/26078
def main():
    print(cv.getBuildInformation())

    points_list = [
        [1434, 308], [1434, 309], [1433, 310], [1427, 310], [1427, 312], [1426, 313], [1422, 313], [1422, 314],
        [1421, 315], [1415, 315], [1415, 316], [1414, 317], [1408, 317], [1408, 319], [1407, 320], [1403, 320],
        [1403, 321], [1402, 322], [1396, 322], [1396, 323], [1395, 324], [1389, 324], [1389, 326], [1388, 327],
        [1382, 327], [1382, 328], [1381, 329], [1376, 329], [1376, 330], [1375, 331], [1369, 331], [1369, 333],
        [1368, 334], [1362, 334], [1362, 335], [1361, 336], [1359, 336], [1359, 1016], [1365, 1016], [1366, 1017],
        [1366, 1019], [1430, 1019], [1430, 1017], [1431, 1016], [1440, 1016], [1440, 308]
    ]
    points = np.array(points_list)

    ellipse_params = cv.fitEllipse(points)
    ellipse_params_ams = cv.fitEllipseAMS(points)
    ellipse_params_direct = cv.fitEllipseDirect(points)
    print(f"fitEllipse={ellipse_params}")
    print(f"fitEllipseAMS={ellipse_params_ams}")
    print(f"fitEllipseDirect={ellipse_params_direct}")

    fitting_error = getEllipseFittingError(points, ellipse_params)
    fitting_ams_error = getEllipseFittingError(points, ellipse_params_ams)
    fitting_direct_error = getEllipseFittingError(points, ellipse_params_direct)

    ellipse_points_cv = getEllipsePointsCV(ellipse_params)
    ellipse_points_cv_ams = getEllipsePointsCV(ellipse_params_ams)
    ellipse_points_cv_direct = getEllipsePointsCV(ellipse_params_direct)

    # draw distance map
    dist_map = drawEllipseDistanceMap(points, ellipse_params)
    cv.imwrite("dist_map.png", dist_map)

    dist_map_ams = drawEllipseDistanceMap(points, ellipse_params_ams)
    cv.imwrite("dist_map_ams.png", dist_map_ams)

    dist_map_direct = drawEllipseDistanceMap(points, ellipse_params_direct)
    cv.imwrite("dist_map_direct.png", dist_map_direct)

    _, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(points[:, 0], points[:, 1], c='blue', label='Points')

    ellipse_polygon = plt.Polygon(ellipse_points_cv, fill=None, edgecolor='red', \
                                  label='Fitted Ellipse (error={:.2f})'.format(fitting_error))
    ax.add_patch(ellipse_polygon)

    ellipse_polygon_ams = plt.Polygon(ellipse_points_cv_ams, fill=None, edgecolor='green', \
                                      label='Fitted Ellipse (AMS) (error={:.2f})'.format(fitting_ams_error))
    ax.add_patch(ellipse_polygon_ams)

    ellipse_polygon_direct = plt.Polygon(ellipse_points_cv_direct, fill=None, edgecolor='blue', \
                                         label='Fitted Ellipse (Direct) (error={:.2f})'.format(fitting_direct_error))
    ax.add_patch(ellipse_polygon_direct)

    # ax.set_aspect('equal', adjustable='box')
    ax.legend()
    plt.show()

if __name__ == '__main__':
    main()