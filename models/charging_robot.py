"""
-------------------------------------------------
文件名：charging_robot.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块定义了充电机器人 (`ChargingRobot`)，用于为园区内停在车位上的车辆提供自动充电服务。
    机器人具备移动能力，可以前往指定车辆并执行充电任务，充电过程受充电速度、电池系数、调度策略等因素影响。
-------------------------------------------------
"""

class ChargingRobot:
    def __init__(self, robot_id, position, battery_level=100, max_battery=100, move_speed=2, 
                 charge_efficiency=0.95, min_battery_threshold=20, station_position=None): 
        """
        充电机器人类，负责移动、充电、管理自身电量。

        :param charge_efficiency: 机器人充电效率（损耗 5% 能量）
        """
        self.id = robot_id
        self.position = position
        self.battery_level = battery_level
        self.max_battery = max_battery
        self.move_speed = move_speed
        self.charge_efficiency = charge_efficiency
        self.min_battery_threshold = min_battery_threshold
        self.station_position = station_position
        self.target_vehicle = None
        self.status = "idle"
        self.route = []

    def charging_vehicle(self):
        """ 
        充电机器人给车辆充电，消耗自身电量
        该函数每次单位间隔调用一次。
        """
        if self.target_vehicle and self.status == "charging_vehicle":
            charge_rate = self.target_vehicle.get_charging_speed()
            self.target_vehicle.charging(charge_rate)

            # 机器人电量消耗受车辆电池系数影响
            self.battery_level -= charge_rate / self.charge_efficiency
            
            if self.target_vehicle.charging_status == "charged":
                self.status = "idle"
                self.target_vehicle = None  # 任务完成

    def compute_route_to_target(self, target_pos):
        """计算机器人自由移动到目标车辆位置的路径，不受道路限制"""
        self.route = []
        x, y = self.position
        target_x, target_y = target_pos

        while x != target_x:
            x += 1 if x < target_x else -1
            self.route.append((x, y))

        while y != target_y:
            y += 1 if y < target_y else -1
            self.route.append((x, y))

        if self.route:
            self.status = "moving"

    def move_along_route(self):
        """机器人沿路径移动一步"""
        if self.route and self.status == "moving":
            self.position = self.route.pop(0)
            if not self.route:
                self.status = "charging_vehicle"

    def update(self):
        """根据机器人当前状态执行对应的更新操作，每次刷新调用一次"""
        if self.status == "moving":
            self.move_along_route()
        elif self.status == "charging_vehicle":
            self.charging_vehicle()
        elif self.status == "idle":
            # 空闲时可以检查电量是否需要返回充电站，或等待新任务
            pass

