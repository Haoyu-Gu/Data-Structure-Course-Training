"""
-------------------------------------------------
文件名：scheduler.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块定义了调度器 (`Scheduler`)，用于管理园区内的充电机器人调度任务。
    调度器负责分配充电机器人，确保充电任务合理分配，并优化充电效率。
-------------------------------------------------
"""
import numpy as np

def nearest_task_first(robots, vehicles):
    """
    充电策略 1: 最近任务优先
    机器人优先选择离自己最近的车辆。

    :param robots: 充电机器人列表
    :param vehicles: 需要充电的车辆列表
    :return: 任务分配字典 {robot: vehicle}
    """
    task_assignment = {}  # 存储机器人到车辆的映射
    available_vehicles = vehicles[:]  # 复制车辆列表，防止修改原列表

    for robot in robots:
        if robot.status in ["idle", "recharging"]:  # 仅空闲机器人才分配任务
            min_distance = float('inf')
            selected_vehicle = None

            for vehicle in available_vehicles:
                distance = np.linalg.norm(np.array(robot.position) - np.array(vehicle.position))
                if distance < min_distance:
                    min_distance = distance
                    selected_vehicle = vehicle

            if selected_vehicle:
                task_assignment[robot] = selected_vehicle
                available_vehicles.remove(selected_vehicle)  # 确保每辆车只被一个机器人服务

    return task_assignment


def max_demand_first(robots, vehicles):
    """
    充电策略 2: 最大需求优先
    机器人优先选择充电需求最大的车辆（charge_needed - battery_level 最大）。

    :param robots: 充电机器人列表
    :param vehicles: 需要充电的车辆列表
    :return: 任务分配字典 {robot: vehicle}
    """
    task_assignment = {}  # 存储机器人到车辆的映射
    available_vehicles = sorted(vehicles, key=lambda v: v.charge_needed - v.battery_level, reverse=True)  # 按需求排序

    for robot in robots:
        if robot.status in ["idle", "recharging"]:  # 仅空闲机器人才分配任务
            if available_vehicles:
                selected_vehicle = available_vehicles.pop(0)  # 选择需求最大的车辆
                task_assignment[robot] = selected_vehicle

    return task_assignment