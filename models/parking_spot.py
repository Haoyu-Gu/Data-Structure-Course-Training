"""
文件名：parking_spot.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块定义了车位 (`ParkingSpot`) 类，表示园区内的停车位。
    每个车位具有固定的尺寸（`4×2`），可以被车辆占用或释放，并记录车位的方向（水平/垂直）。
"""
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