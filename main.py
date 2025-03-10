"""
-------------------------------------------------
文件名：main.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该文件是整个模拟系统的入口点，负责：
    - 初始化 `Simulation`（智能园区）
    - 启动 `run_gui()` 进行可视化渲染
    - 运行园区动态模拟，包括车辆移动和充电机器人调度
-------------------------------------------------
"""
from simulation import Simulation
from render import run_gui

def main():
    # 可以根据需求调整 grid_size、num_buildings、num_stations、num_gates 等参数
    sim = Simulation(grid_size=(200, 200), num_buildings=2, num_stations=2, num_gates=3)
    run_gui(sim)

if __name__ == '__main__':
    main()