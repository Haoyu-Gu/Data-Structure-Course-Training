"""
-------------------------------------------------
文件名：simulation.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块管理园区的整体模拟，包括：
    - 生成园区布局（道路、车位、建筑、大门、充电桩）
    - 车辆从大门进入，选择车位，沿道路行驶
    - 充电机器人自动调度，为低电量车辆提供充电
    - 车辆充电完成后离开，释放车位
-------------------------------------------------
"""
import numpy as np
import random

from models.parking_spot import ParkingSpot
from models.vehicle import Vehicle
from models.charging_robot import ChargingRobot

class Simulation:
    def __init__(self, grid_size=(50, 50), num_buildings=2, num_stations=2, num_gates=3):
        self.grid_size = grid_size
        self.num_buildings = num_buildings
        self.num_stations = num_stations
        self.num_gates = num_gates

        self.map = np.full(self.grid_size, "S")
        self.parking_spots = []
        self.gates = []
        self.vehicles = []

        self.global_time = 0
        self.spawn_interval = 10
        self.gate_spawn_prob = [0.5, 0.3, 0.2]

        self.road_offset = 4
        self.road_width = 4  # 道路宽度4格（内外各2格）
        self._generate_inner_ring_roads()
        self._generate_parking_spots()
        self._generate_gates()
        self._generate_buildings()
        self._generate_charging_stations()

        # 假设在模拟初始化时添加机器人到指定的初始位置
        self.robots = [
            ChargingRobot(robot_id=1, position=(10, 10), station_position=(10, 10)),
            ChargingRobot(robot_id=2, position=(20, 20), station_position=(20, 20)),
            ChargingRobot(robot_id=2, position=(30, 30), station_position=(25, 25)),
        ]

    def _generate_inner_ring_roads(self):
        w, h = self.grid_size
        rw = self.road_offset
        # 四边铺设4格宽的道路
        self.map[rw:h-rw, rw:rw+4] = "R"
        self.map[rw:h-rw, w-rw-4:w-rw] = "R"
        self.map[rw:rw+4, rw:w-rw] = "R"
        self.map[h-rw-4:h-rw, rw:w-rw] = "R"

        # 四角恢复为空闲区
        self.map[:rw, :rw] = "S"
        self.map[:rw, w-rw:] = "S"
        self.map[h-rw:, :rw] = "S"
        self.map[h-rw:, w-rw:] = "S"

    def _generate_parking_spots(self):
        w, h = self.grid_size
        rw = self.road_offset

        # 顶部 & 底部车位（宽2，高4）
        for x in range(rw+2, w-rw-2, 2):
            self.parking_spots.append(ParkingSpot(x, 0, x+2, 4, is_horizontal=False))
            self.parking_spots.append(ParkingSpot(x, h-4, x+2, h, is_horizontal=False))

        # 左侧 & 右侧车位（宽4，高2）
        for y in range(rw+2, h-rw-2, 2):
            self.parking_spots.append(ParkingSpot(0, y, 4, y+2, is_horizontal=True))
            self.parking_spots.append(ParkingSpot(w-4, y, w, y+2, is_horizontal=True))

    def _generate_gates(self):
        w, h = self.grid_size
        # 对各边停车位排序，便于取连续3个
        top_spots = sorted([s for s in self.parking_spots if s.y1 == 0], key=lambda s: s.x1)
        bottom_spots = sorted([s for s in self.parking_spots if s.y2 == h], key=lambda s: s.x1)
        left_spots = sorted([s for s in self.parking_spots if s.x1 == 0], key=lambda s: s.y1)
        right_spots = sorted([s for s in self.parking_spots if s.x2 == w], key=lambda s: s.y1)

        candidates = []
        if len(top_spots) >= 3:
            candidates.append(('top', top_spots))
        if len(bottom_spots) >= 3:
            candidates.append(('bottom', bottom_spots))
        if len(left_spots) >= 3:
            candidates.append(('left', left_spots))
        if len(right_spots) >= 3:
            candidates.append(('right', right_spots))

        chosen = random.sample(candidates, min(len(candidates), self.num_gates))
        for edge, spots in chosen:
            start_idx = random.randint(0, len(spots) - 3)
            selected = spots[start_idx:start_idx+3]
            if edge in ('top', 'bottom'):
                x1 = selected[0].x1
                x2 = selected[-1].x2
                y1 = selected[0].y1
                y2 = selected[0].y2
            else:
                y1 = selected[0].y1
                y2 = selected[-1].y2
                x1 = selected[0].x1
                x2 = selected[0].x2
            self.map[y1:y2, x1:x2] = "G"
            self.gates.append((x1, y1, x2, y2))

    def _generate_buildings(self):
        w, h = self.grid_size
        for _ in range(self.num_buildings):
            bx = random.randint(self.road_offset+5, w - self.road_offset - 10)
            by = random.randint(self.road_offset+5, h - self.road_offset - 10)
            bw = random.randint(3, 6)
            bh = random.randint(3, 6)
            if np.all(self.map[by:by+bh, bx:bx+bw] == "S"):
                self.map[by:by+bh, bx:bx+bw] = "B"

    def _generate_charging_stations(self):
        for _ in range(self.num_stations):
            ys, xs = np.where(self.map == "S")
            if len(xs) > 0:
                idx = random.randint(0, len(xs)-1)
                self.map[ys[idx], xs[idx]] = "C"

    # ====== BFS 寻路（仅走 'R' 或 'G'）=====
    def _compute_path_on_road(self, start, end):
        w, h = self.grid_size
        if not self._is_driveable(start) or not self._is_driveable(end):
            return None

        from collections import deque
        queue = deque()
        visited = set()
        parent = {}
        queue.append(start)
        visited.add(start)
        directions = [(0,1), (0,-1), (1,0), (-1,0)]
        found = False

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == end:
                found = True
                break
            for dx, dy in directions:
                nx, ny = cx+dx, cy+dy
                if 0 <= nx < w and 0 <= ny < h:
                    if (nx, ny) not in visited and self._is_driveable((nx, ny)):
                        visited.add((nx, ny))
                        parent[(nx, ny)] = (cx, cy)
                        queue.append((nx, ny))

        if not found:
            return None

        # 回溯
        path = []
        cur = end
        while cur != start:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path

    def _is_driveable(self, pos):
        x, y = pos
        if x < 0 or x >= self.grid_size[0] or y < 0 or y >= self.grid_size[1]:
            return False
        cell = self.map[y, x]
        return cell in ("R", "G")

    # ====== 内道和外道车道循环 ======
    def get_inner_loop(self):
        """
        内道（顺时针车辆走），位于靠内侧的 2 像素：
        上边：y = road_offset+3
        右边：x = w-road_offset-3
        下边：y = h-road_offset-3
        左边：x = road_offset+3
        顺时针顺序：上 -> 右 -> 下 -> 左
        """
        w, h = self.grid_size
        rw = self.road_offset

        top_inner = [(x, rw+3) for x in range(rw+2, w-rw-1)]
        right_inner = [(w-rw-3, y) for y in range(rw+2, h-rw-1)]
        bottom_inner = [(x, h-rw-3) for x in range(w-rw-2, rw+1, -1)]
        left_inner = [(rw+3, y) for y in range(h-rw-2, rw+1, -1)]

        return top_inner + right_inner + bottom_inner + left_inner

    def get_outer_loop(self):
        """
        外道（逆时针车辆走），位于靠外侧的 2 像素：
        上边：y = road_offset+1
        左边：x = road_offset+1
        下边：y = h-road_offset-1
        右边：x = w-road_offset-1
        逆时针顺序：上(右到左) -> 左(上到下) -> 下(左到右) -> 右(下到上)
        """
        w, h = self.grid_size
        rw = self.road_offset

        top_ccw = [(x, rw+1) for x in range(w-rw-2, rw+1, -1)]
        left_ccw = [(rw+1, y) for y in range(rw+2, h-rw-1)]
        bottom_ccw = [(x, h-rw-1) for x in range(rw+2, w-rw-1)]
        right_ccw = [(w-rw-1, y) for y in range(h-rw-2, rw+1, -1)]

        return top_ccw + left_ccw + bottom_ccw + right_ccw

    # ====== 公共方法 ======
    def get_map_data(self):
        return self.map

    def get_parking_spots(self):
        return self.parking_spots

    def get_gates(self):
        return self.gates

    def get_empty_parking_spots(self):
        return [s for s in self.parking_spots if not s.is_occupied]

    def get_parking_adjacent_position(self, spot):
        w, h = self.grid_size
        cx = (spot.x1 + spot.x2) // 2
        cy = (spot.y1 + spot.y2) // 2

        if spot.y1 == 0:
            return (cx, spot.y2)
        elif spot.y2 == h:
            return (cx, spot.y1 - 1)
        elif spot.x1 == 0:
            return (spot.x2, cy)
        elif spot.x2 == w:
            return (spot.x1 - 1, cy)
        else:
            return (cx, cy)

    def get_spawn_position_for_gate(self, gate):
        """
        返回位于道路中线的生成点，保证车辆可随机贴靠到内道或外道
        """
        x1, y1, x2, y2 = gate
        w, h = self.grid_size
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        rw = self.road_offset

        if y1 == 0:
            return (cx, rw+2)
        elif y2 == h:
            return (cx, h - rw - 2)
        elif x1 == 0:
            return (rw+2, cy)
        elif x2 == w:
            return (w - rw - 2, cy)
        else:
            return (cx, cy)

    def update(self):
        self.global_time += 1

        if self.global_time % self.spawn_interval == 0:
            for i, gate in enumerate(self.gates):
                prob = self.gate_spawn_prob[i] if i < len(self.gate_spawn_prob) else 0
                if random.random() < prob:
                    spawn_pos = self.get_spawn_position_for_gate(gate)
                    empties = self.get_empty_parking_spots()

                    if empties:
                        chosen_spot = random.choice(empties)
                        target_pos = self.get_parking_adjacent_position(chosen_spot)
                        parking_time = random.randint(15, 40)
                        # 备用 BFS (实际会被车辆内部的车道行驶策略覆盖)
                        route = self._compute_path_on_road(spawn_pos, target_pos)
                        if not route:
                            route = []

                        v = Vehicle(
                            simulation=self,
                            origin_gate=gate,
                            spawn_pos=spawn_pos,
                            target_pos=target_pos,
                            parking_duration=parking_time,
                            spawn_time=self.global_time,
                            route=route
                        )
                        self.vehicles.append(v)

        for v in self.vehicles[:]:
            v.update()
            if v.state == "exited":
                self.vehicles.remove(v)
        
        for robot in self.robots:
            robot.update()