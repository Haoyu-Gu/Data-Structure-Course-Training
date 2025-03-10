"""
-------------------------------------------------
文件名：vehicle.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块定义了车辆 (`Vehicle`) 类，表示在园区内行驶和充电的车辆。
    车辆会从大门 (`G`) 处刷新，并按照设定的行驶方向（顺时针/逆时针）前往目标车位 (`ParkingSpot`)。
    车辆具有电池特性，并在低电量时请求充电。
-------------------------------------------------
"""

import math
import random

class Vehicle:
    def __init__(self, simulation, origin_gate, spawn_pos, target_pos, parking_duration, spawn_time, route=None):
        """
        :param simulation: Simulation 实例
        :param origin_gate: 大门区域 (x1, y1, x2, y2)
        :param spawn_pos: 生成点（来自大门），位于道路中线
        :param target_pos: 目标停车位旁位置
        :param parking_duration: 停车时长
        :param spawn_time: 生成时刻
        :param route: 备用路径（内部将使用车道循环覆盖）
        """
        self.sim = simulation
        self.origin_gate = origin_gate
        self.spawn_pos = spawn_pos
        self.target_pos = target_pos
        self.parking_duration = parking_duration
        self.spawn_time = spawn_time

        # 车辆状态: entering -> parked -> exiting -> exited
        self.state = "entering"
        self.parked_time = None
        self.bound_spot = None

        # 随机分配方向：True=顺时针(内道)，False=逆时针(外道)
        self.clockwise = random.choice([True, False])
        if self.clockwise:
            lane_loop = self.sim.get_inner_loop()
        else:
            lane_loop = self.sim.get_outer_loop()

        # 将生成点贴靠到对应车道上
        self.position = min(
            lane_loop,
            key=lambda p: math.hypot(p[0] - spawn_pos[0], p[1] - spawn_pos[1])
        )

        # 计算进入路线：将目标位置也贴靠到车道
        target_lane = min(
            lane_loop,
            key=lambda p: math.hypot(p[0] - target_pos[0], p[1] - target_pos[1])
        )
        start_index = self.find_index(lane_loop, self.position)
        end_index = self.find_index(lane_loop, target_lane)
        self.route = self.compute_loop_route(lane_loop, start_index, end_index)

        # 车辆朝向/道路边侧，用于渲染微调
        self.orientation = "horizontal"
        self.road_side = None
        self.debug_info = ""
        self._detect_road_side()

    def find_index(self, loop, pos):
        distances = [math.hypot(p[0] - pos[0], p[1] - pos[1]) for p in loop]
        return distances.index(min(distances))

    def compute_loop_route(self, loop, start_index, end_index):
        # 从 start_index 到 end_index 的顺序段（若 start > end，则跨过列表末尾循环）
        if start_index <= end_index:
            return loop[start_index:end_index+1]
        else:
            return loop[start_index:] + loop[:end_index+1]

    def _compute_simple_manhattan(self, start, end):
        # 备用方法（目前不使用）
        route = []
        sx, sy = start
        ex, ey = end
        if sx < ex:
            for x in range(sx, ex):
                route.append((x+1, sy))
        else:
            for x in range(sx, ex, -1):
                route.append((x-1, sy))
        if sy < ey:
            for y in range(sy, ey):
                route.append((ex, y+1))
        else:
            for y in range(sy, ey, -1):
                route.append((ex, y-1))
        return route

    def update(self):
        if self.state == "entering":
            # 沿 route 前进
            if self.route:
                self.position = self.route.pop(0)
            else:
                # 抵达停车位邻近位置 => parked
                self.state = "parked"
                self.parked_time = self.sim.global_time
                for s in self.sim.get_parking_spots():
                    if (not s.is_occupied
                        and self.sim.get_parking_adjacent_position(s) == self.target_pos):
                        s.is_occupied = True
                        self.bound_spot = s
                        break

        elif self.state == "parked":
            # 停够时长后 => exiting
            if (self.sim.global_time - self.parked_time) >= self.parking_duration:
                self.state = "exiting"

                if self.clockwise:
                    lane_loop = self.sim.get_inner_loop()
                else:
                    lane_loop = self.sim.get_outer_loop()

                # 离场时：目标为大门 spawn 点（贴靠）
                exit_point = self.sim.get_spawn_position_for_gate(self.origin_gate)
                exit_lane = min(
                    lane_loop,
                    key=lambda p: math.hypot(p[0] - exit_point[0], p[1] - exit_point[1])
                )
                current_index = self.find_index(lane_loop, self.position)
                exit_index = self.find_index(lane_loop, exit_lane)
                self.route = self.compute_loop_route(lane_loop, current_index, exit_index)

        elif self.state == "exiting":
            if self.route:
                self.position = self.route.pop(0)
            else:
                # 抵达大门 => exited
                self.state = "exited"
                if self.bound_spot:
                    self.bound_spot.is_occupied = False

        elif self.state == "exited":
            pass

        # 每次更新都检测车朝向和所处的道路边
        self._update_orientation()
        self._detect_road_side()

    def _update_orientation(self):
        if self.state in ("entering", "exiting") and self.route:
            cx, cy = self.position
            nx, ny = self.route[0]
            self.orientation = "horizontal" if nx != cx else "vertical"

    def _detect_road_side(self):
        """
        根据当前坐标判断在道路的 top/bottom/left/right 边，
        用于渲染 offset 微调
        """
        w, h = self.sim.grid_size
        rw = self.sim.road_width
        x, y = self.position

        if rw <= y < rw+4:
            self.road_side = "top"
        elif (h - rw - 4) <= y < (h - rw):
            self.road_side = "bottom"
        elif rw <= x < rw+4:
            self.road_side = "left"
        elif (w - rw - 4) <= x < (w - rw):
            self.road_side = "right"
        else:
            self.road_side = None

    def get_render_offset(self):
        """
        根据你提出的需求：
         - 在左右道路行驶时 (left/right)，横坐标 -1
         - 在上下道路行驶时 (top/bottom)，纵坐标 +1
        """
        if self.road_side in ("left", "right"):
            return (-5, 0)
        elif self.road_side in ("top", "bottom"):
            return (0, -5)
        else:
            return (0, 0)

    def get_current_orientation(self):
        return self.orientation

    def get_debug_info(self):
        return f"State={self.state}, pos={self.position}, road_side={self.road_side}"