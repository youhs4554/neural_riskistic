import math
from types import SimpleNamespace
import cv2


def bb_intersection_over_union(boxA, boxB):
    # determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    # compute the area of intersection rectangle
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    # compute the area of both the prediction and ground-truth
    # rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = interArea / float(boxAArea + boxBArea - interArea)
    # return the intersection over union value
    return iou


class DetectionVisualization():
    classes = 80

    def __init__(self):
        self.colors = [
            [1, 0, 1], [0, 0, 1],
            [0, 1, 1], [0, 1, 0],
            [1, 1, 0], [1, 0, 0]
        ]

    def get_color(self, c, x, max_num):
        """
        Getting color based on yolo src
        """
        ratio = 5*(float(x)/max_num)
        i = int(math.floor(ratio))
        j = int(math.ceil(ratio))
        ratio -= i
        r = (1 - ratio) * self.colors[i][c] + ratio*self.colors[j][c]
        return int(255*r)

    def draw_detections(self, img, yolo_results):
        """
        drawing result of yolo
        """

        _, height, _ = img.shape
        for yolo_result in yolo_results:
            yolo_result = SimpleNamespace(**yolo_result)
            bbox = SimpleNamespace(**yolo_result.bounding_box)

            class_index = yolo_result.class_index
            obj_name = yolo_result.obj_name

            x = bbox.x_min
            y = bbox.y_min
            w = bbox.width
            h = bbox.height

            offset = class_index * 123457 % self.classes

            red = self.get_color(2, offset, self.classes)
            green = self.get_color(1, offset, self.classes)
            blue = self.get_color(0, offset, self.classes)
            box_width = int(height * 0.006)
            cv2.rectangle(img, (int(x), int(y)), (int(x+w)+1,
                                                  int(y+h)+1), (red, green, blue), box_width)
            cv2.putText(
                img, obj_name,
                (int(x) - 2, int(y) - 5),
                cv2.FONT_HERSHEY_COMPLEX,
                0.8, (red, green, blue),
                2, cv2.LINE_AA
            )

        return img
