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

    def charge_vehicle(self):
        """ 充电机器人给车辆充电，消耗自身电量 """
        if self.target_vehicle and self.status == "charging":
            charge_amount = self.target_vehicle.charging_speed()
            self.target_vehicle.charge(charge_amount)

            # 机器人电量消耗受 车辆电池系数 影响
            self.battery_level -= charge_amount / self.charge_efficiency * self.target_vehicle.battery_coefficient
            
            if self.target_vehicle.charging_status == "charged":
                self.status = "idle"
                self.target_vehicle = None  # 任务完成

