# models/parking_spot.py

class ParkingSpot:
    def __init__(self, x1, y1, x2, y2, is_horizontal=True):
        """
        表示园区内的一个车位:
        (x1, y1) ~ (x2, y2) 为格子坐标区间
        :param is_horizontal: True 表示车位水平方向，False 表示竖直方向
        """
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.is_horizontal = is_horizontal
        self.is_occupied = False