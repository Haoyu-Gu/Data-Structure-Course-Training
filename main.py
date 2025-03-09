# main.py
from simulation import Simulation
from render import run_gui

def main():
    # 可以根据需求调整 grid_size、num_buildings、num_stations、num_gates 等参数
    sim = Simulation(grid_size=(200, 200), num_buildings=2, num_stations=2, num_gates=3)
    run_gui(sim)

if __name__ == '__main__':
    main()