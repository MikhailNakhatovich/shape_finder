import argparse
import cv2
import numpy as np


BORDER_WIDTH = 50
EPS_APPROXIMATION = 2e-2
EPS_ZERO = 1e-6


def read_shapes(shapes_file_name):
    with open(shapes_file_name) as shapes_file:
        shapes = []
        n = int(shapes_file.readline())
        for i in range(n):
            shape_coords = list(map(int, shapes_file.readline().split(', ')))
            shape_vertexes = np.array(shape_coords).reshape((-1, 2))
            if cv2.contourArea(shape_vertexes, True) < 0:
                shape_vertexes = shape_vertexes[::-1]
            shapes.append(shape_vertexes)
        return shapes


def process_image(image):
    image = cv2.copyMakeBorder(image, BORDER_WIDTH, BORDER_WIDTH, BORDER_WIDTH, BORDER_WIDTH,
                               cv2.BORDER_CONSTANT, value=0)
    contours, hierarchy = cv2.findContours(image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    contours = np.array(contours)[hierarchy[0, :, 3] != -1]
    new_image = np.ones_like(image)
    cv2.drawContours(new_image, contours, -1, 0, -1)
    image[new_image.astype(bool)] = 255
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def find_polygons(image):
    polygons = []
    contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours[:-1]:
        polygon = cv2.approxPolyDP(contour, EPS_APPROXIMATION * cv2.arcLength(contour, True), True)
        polygons.append(np.squeeze(polygon, 1))
    return polygons


def find_angle(polygon, shape):
    x_p, y_p = (polygon[1] - polygon[0]) / np.linalg.norm(polygon[1] - polygon[0])
    x_s, y_s = (shape[1] - shape[0]) / np.linalg.norm(shape[1] - shape[0])
    if np.abs(x_s) <= EPS_ZERO:
        sin_angle, cos_angle = -x_p / y_s, y_p / y_s
    elif np.abs(y_s) <= EPS_ZERO:
        sin_angle, cos_angle = y_p / x_s, x_p / x_s
    else:
        sin_angle, cos_angle = (y_p / y_s - x_p / x_s) / (x_s / y_s + y_s / x_s), \
                               (x_p / y_s + y_p / x_s) / (x_s / y_s + y_s / x_s)
    angle = np.arcsin(sin_angle)
    if cos_angle < 0:
        angle = np.pi - angle
    return angle


def find_bias(polygon, shape, scale, angle):
    x_p, y_p = polygon[0]
    x_s, y_s = shape[0] * scale
    bias_x, bias_y = x_p - (x_s * np.cos(angle) - y_s * np.sin(angle)), \
                     y_p - (x_s * np.sin(angle) + y_s * np.cos(angle))
    return bias_x, bias_y


def find_max_dist(polygon, shape, scale, angle, bias_x, bias_y):
    max_dist = 0
    for polygon_vertex, shape_vertex in zip(polygon, shape):
        x_s, y_s = shape_vertex * scale
        x_s_t, y_s_t = bias_x + (x_s * np.cos(angle) - y_s * np.sin(angle)), \
                       bias_y + (x_s * np.sin(angle) + y_s * np.cos(angle))
        max_dist = max(max_dist, np.linalg.norm(polygon_vertex - (x_s_t, y_s_t)))
    return max_dist


def find_primitives(shapes, polygons):
    primitives = []
    for polygon in polygons:
        min_max_dist = np.inf
        for _ in range(polygon.shape[0]):
            for j, shape in enumerate(shapes):
                if polygon.shape[0] == shape.shape[0]:
                    scale = np.sqrt(cv2.contourArea(polygon) / cv2.contourArea(shape))
                    angle = find_angle(polygon, shape)
                    bias_x, bias_y = find_bias(polygon, shape, scale, angle)
                    max_dist = find_max_dist(polygon, shape, scale, angle, bias_x, bias_y)
                    if max_dist < min_max_dist:
                        min_max_dist = max_dist
                        min_j, min_bias_x, min_bias_y, min_scale, min_angle = j, bias_x, bias_y, scale, angle
            polygon = np.roll(polygon, 1, 0)
        if min_max_dist < np.inf:
            primitives.append([min_j, min_bias_x - BORDER_WIDTH, min_bias_y - BORDER_WIDTH,
                               min_scale, min_angle * 180 / np.pi])
    return np.round(primitives).astype(int)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find shapes in the image')
    parser.add_argument('-s', '--shapes_file_name', help='Shapes file name')
    parser.add_argument('-i', '--image_name', help='Image name')
    args = parser.parse_args()

    shapes = read_shapes(args.shapes_file_name)

    image = cv2.imread(args.image_name, cv2.IMREAD_GRAYSCALE)

    image = process_image(image)

    polygons = find_polygons(image)

    primitives = find_primitives(shapes, polygons)

    print(primitives.shape[0])
    for primitive in primitives:
        print(*primitive, sep=', ')
