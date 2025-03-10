"""
-------------------------------------------------
文件名：render.py
创作人：顾昊瑜
日期：2025年3月
功能描述：
    该模块使用 PyQt5 进行可视化渲染，动态展示园区的布局和车辆移动情况。
    - 采用 100ms 刷新率，实时更新车辆位置
    - 可视化园区结构，包括道路、车位、建筑、大门、充电桩
    - 动态展示车辆的行驶过程
-------------------------------------------------
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QTimer

class ParkRenderer(QWidget):
    def __init__(self, simulation):
        super().__init__()
        self.simulation = simulation
        self.map_data = simulation.get_map_data()
        self.cell_size = 5

        rows, cols = self.map_data.shape
        # 根据地图尺寸设置窗口大小
        self.setFixedSize(cols * self.cell_size, rows * self.cell_size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color_map = {
            "R": QColor(128, 128, 128),  # 道路
            "B": QColor(0, 0, 0),        # 建筑
            "S": QColor(255, 255, 255),  # 空闲区
            "C": QColor(0, 0, 255),      # 充电桩
            "G": QColor(255, 165, 0)     # 大门
        }

        rows, cols = self.map_data.shape

        # 绘制地图背景
        for r in range(rows):
            for c in range(cols):
                cell = self.map_data[r, c]
                painter.setBrush(color_map.get(cell, QColor(200, 200, 200)))
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    c * self.cell_size,
                    r * self.cell_size,
                    self.cell_size,
                    self.cell_size
                )

        # 绘制车位（若覆盖大门则跳过）
        for spot in self.simulation.get_parking_spots():
            if self.map_data[spot.y1, spot.x1] == "G":
                continue
            color = QColor(0, 255, 0) if not spot.is_occupied else QColor(255, 0, 0)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)

            x_pix = spot.x1 * self.cell_size
            y_pix = spot.y1 * self.cell_size
            w_pix = (spot.x2 - spot.x1) * self.cell_size
            h_pix = (spot.y2 - spot.y1) * self.cell_size
            painter.drawRect(x_pix, y_pix, w_pix, h_pix)

        # 绘制车辆（仅 entering/exiting）
        for v in self.simulation.vehicles:
            if v.state in ("entering", "exiting"):
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(128, 0, 128))

                orientation = v.get_current_orientation()
                if orientation == "horizontal":
                    w_cells, h_cells = 4, 2
                else:
                    w_cells, h_cells = 2, 4

                x_pix = v.position[0] * self.cell_size
                y_pix = v.position[1] * self.cell_size

                # 根据车辆 road_side 做微调
                dx, dy = v.get_render_offset()
                x_pix += dx
                y_pix += dy

                painter.drawRect(
                    x_pix,
                    y_pix,
                    w_cells * self.cell_size,
                    h_cells * self.cell_size
                )

                # 如需调试，可在图上绘制文字
                # debug_str = v.get_debug_info()
                # painter.setPen(Qt.black)
                # painter.drawText(x_pix, y_pix, debug_str)

class ParkSimulationWindow(QMainWindow):
    def __init__(self, simulation):
        super().__init__()
        self.setWindowTitle("园区仿真 —— 内外车道顺逆时针（自定义渲染偏移）")
        layout = QVBoxLayout()

        self.renderer = ParkRenderer(simulation)
        layout.addWidget(self.renderer)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # 启动定时器，周期更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(100)

    def on_timer(self):
        self.renderer.simulation.update()
        self.renderer.update()

def run_gui(simulation):
    app = QApplication(sys.argv)
    window = ParkSimulationWindow(simulation)
    window.show()
    sys.exit(app.exec_())