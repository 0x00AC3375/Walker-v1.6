import pygame
import numpy as np
import sys
import os
from collections import deque
import math
import ctypes

# Resource helpers
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# icon
def load_icon(icon = "./logo.ico"):
    try:
        icon_path = resource_path(icon)
        return pygame.image.load(icon_path)
    except:
        return None

# i18n
class I18n:
    def __init__(self, language = "zh-cn"):
        self.language = language
        self.texts = {}
        self.load_language(language = language)
    def load_language(self, language = "zh-cn") -> dict[str, str]:
        try:
            texts = {}
            language_path = resource_path(f"./i18n.{language}.txt")
            if os.path.exists(language_path):
                with open(language_path, "r", encoding = "utf-8") as f:
                    lines = f.readlines()
                    for ln in lines:
                        ln = ln.split("=")
                        # print(len(ln))
                        ln[1] = ln[1].strip()
                        if ln[1] != "":
                            texts[ln[0]] = ln[1] 
            self.texts = texts
        except Exception as e:
            print(e)
            pass

language_select = ["en-us", "zh-cn", "zh-tw", "ja-jp"] # coming soon
i18ns = {item: I18n(language = item) for item in language_select}
current_language = 0
i18n = i18ns[language_select[current_language]]

# fonts
def load_font(font = "./Sen-Regular.otf", size = 20):
    try:
        font_path = resource_path(font)
        return pygame.font.Font(font_path, size = size)
    except:
        return pygame.font.SysFont("Segoe UI Emoji", size)

# --------------------------------
# 计时器
# --------------------------------
class Stopwatch:
    def __init__(self):
        self.reset()
    
    def start(self):
        """启动秒表"""
        if not self.running:
            self.running = True
            if self.start_time == 0:  # 第一次启动
                self.start_time = pygame.time.get_ticks()
            else:  # 从暂停恢复
                pause_duration = pygame.time.get_ticks() - self.pause_time
                self.start_time += pause_duration
    
    def pause(self):
        """暂停秒表"""
        if self.running:
            self.running = False
            self.pause_time = pygame.time.get_ticks()
    
    def stop(self):
        """停止秒表（同暂停）"""
        self.pause()
    
    def reset(self):
        """重置秒表"""
        self.running = False
        self.start_time = 0
        self.pause_time = 0
        self.elapsed_before_pause = 0
    
    # 将毫秒数格式化为 天数:小时:分钟:秒钟.毫秒
    def format_ticks(ticks):    
        milliseconds = ticks % 1000
        total_seconds = ticks // 1000
        seconds = total_seconds % 60
        total_minutes = total_seconds // 60
        minutes = total_minutes % 60
        total_hours = total_minutes // 60
        hours = total_hours % 24
        days = total_hours // 24
        return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def get_elapsed_time(self):
        """获取经过的时间（毫秒）"""
        if not self.running:
            if self.start_time == 0:  # 未启动过
                return 0
            else:  # 暂停状态
                return self.pause_time - self.start_time
        else:  # 运行中
            return pygame.time.get_ticks() - self.start_time
    
    def get_formatted_time(self):
        """获取格式化时间 00:00:00.000"""
        elapsed_ms = self.get_elapsed_time()
        return Stopwatch.format_ticks(elapsed_ms)

timer = Stopwatch()

# ————————————————————————————————
# 参数配置
# ————————————————————————————————
L_MEAN = 0.86      # 米/步
EPSILON = 0.06     # 步长波动 ±0.06 m
DELTA = math.pi / 12  # 最大转向角 
TEMPO = 128
MAX_POINTS = 128   # 显示最近轨迹
SCALE = 50.0       # 初始缩放：1 米 = 50 像素
AIR_WALL_X = None
AIR_WALL_Y = None
BUILDING_L = 5.0
STREET_D = 3.0
TURN_ANGLE = None
sound_on = True

params = {
    "L_MEAN": L_MEAN,
    "EPSILON": EPSILON,
    "DELTA": DELTA,
    "TEMPO": TEMPO,
    "MAX_POINTS": MAX_POINTS,
    "BUILDING_L": BUILDING_L,
    "STREET_D": STREET_D,
    "AIR_WALL_X": AIR_WALL_X,
    "AIR_WALL_Y": AIR_WALL_Y,
    "TURN_ANGLE": TURN_ANGLE
}

default = {
    "L_MEAN": 0.86,
    "EPSILON": 0.06,
    "DELTA": math.pi / 12,
    "TEMPO": 128,
    "MAX_POINTS": 128,
    "BUILDING_L": 5.00,
    "STREET_D": 3.00,
    "TURN_ANGLE": None
}

FPS = 60
period = 60000 / params["TEMPO"] # ms

# --------------------------------
# sound fx
# --------------------------------
# sound fx
pygame.mixer.init()
sound_kick   = pygame.mixer.Sound(resource_path("./kick.wav"))
sound_clap   = pygame.mixer.Sound(resource_path("./clap.wav"))
sound_hihat  = pygame.mixer.Sound(resource_path("./hi-hat.wav"))
sound_snare  = pygame.mixer.Sound(resource_path("./snare.wav"))
sound_cymbal = pygame.mixer.Sound(resource_path("./cymbal.wav"))

sound_kick.set_volume(0.4)
sound_clap.set_volume(0.35)
sound_hihat.set_volume(0.25)
sound_snare.set_volume(0.45)
sound_cymbal.set_volume(0.95)

SOUNDS = {
    "kick":   sound_kick,
    "snare":  sound_snare,
    "hihat":  sound_hihat,
    "cowbell":   sound_clap,
    "cymbal": sound_cymbal,
}
sound_volumes = {
    "global": 1.0,
    "kick": 0.4,
    "snare": 0.45,
    "hihat": 0.25,
    "cymbal": 0.95,
    "cowbell": 0.35
}

# ————————————————————————————————
# 文本输入框
# ————————————————————————————————
class TextInput:
    def __init__(self, x, y, w, h, text = ""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = str(text)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isprintable():
                self.text += event.unicode

    def draw(self, screen, font):
        color = (120, 200, 255) if self.active else (180, 180, 180)
        pygame.draw.rect(screen, color, self.rect, 2)
        txt = font.render(self.text, True, TEXT_COLOR)
        screen.blit(txt, (self.rect.x + 6, self.rect.y + 6))

# ————————————————————————————————
# 按钮
# ————————————————————————————————
class Button:
    def __init__(self, x, y, w, h, label, color = (70, 120, 70)):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.color = color

    def clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN and
            self.rect.collidepoint(event.pos)
        )

    def draw(self, screen, font):
        pygame.draw.rect(screen, self.color, self.rect)
        txt = font.render(self.label, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center = self.rect.center))


# ————————————————————————————————
# 初始化 Pygame
# ————————————————————————————————
pygame.init()
pygame.display.set_icon(load_icon())
# enable_dark_title_bar(pygame.display.get_surface())

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except:
    ctypes.windll.user32.SetProcessDPIAware()

PLOT_WIDTH = 1600
PANEL_WIDTH = 400
WIDTH, HEIGHT = 1600, 1200
screen = pygame.display.set_mode((PLOT_WIDTH + PANEL_WIDTH, HEIGHT),)
pygame.display.set_caption("Urban Drift " + os.path.basename(__file__)[:-3] + " by @0x00ac3375")
clock = pygame.time.Clock()

# 颜色定义
BACKGROUND = (32, 32, 32)
AGENT_COLOR = (100, 200, 255)
AXIS_COLOR = (200, 200, 200, 150)  # 坐标轴颜色
GRID_COLOR = (80, 80, 80, 80)      # 网格颜色
TEXT_COLOR = (220, 220, 220)

# --------------------------------
# 初始化 UI
# --------------------------------
ui_x = PLOT_WIDTH + 20
UI_WIDTH = PANEL_WIDTH - 40
BTN_WIDTH = 180
ui_font = load_font("./global.ttf", 18)
title_font = load_font("./global.ttf", 21)
font = load_font("./global.ttf", 18)

inputs = {
    "L_MEAN": TextInput(ui_x, 120, UI_WIDTH, 30, str(L_MEAN)),
    "EPSILON": TextInput(ui_x, 200, UI_WIDTH, 30, str(EPSILON)),
    "DELTA": TextInput(ui_x, 280, UI_WIDTH, 30, f"{DELTA * 180 / math.pi:.2f}"),
    "TEMPO": TextInput(ui_x, 360, UI_WIDTH, 30, str(TEMPO)),
    "MAX_POINTS": TextInput(ui_x, 440, UI_WIDTH, 30, str(MAX_POINTS)),
    "AIR_WALL_X": TextInput(ui_x, 520, UI_WIDTH, 30, ""),
    "AIR_WALL_Y": TextInput(ui_x, 600, UI_WIDTH, 30, ""),
    "BUILDING_L": TextInput(ui_x, 680, UI_WIDTH, 30, str(BUILDING_L)),
    "STREET_D": TextInput(ui_x, 760, UI_WIDTH, 30, str(STREET_D)),
    "TURN_ANGLE": TextInput(ui_x, 840, UI_WIDTH, 30, ""),
}

apply_btn = Button(ui_x, 1080, UI_WIDTH, 40, "Apply", (70, 120, 70))
mesh_btn = Button(80, 1140, BTN_WIDTH, 40, "Mesh: On", (70, 70, 170))
reset_btn = Button(ui_x, 1140, UI_WIDTH, 40, "Reset", (170, 70, 70))
zoom_btn = Button(280, 1140, BTN_WIDTH, 40, "Auto Zoom: On", (70, 170, 170))
sound_btn = Button(480, 1140, BTN_WIDTH, 40, "Sound: On", (170, 170, 70))

# ————————————————————————————————
# 智能坐标轴系统类
# ————————————————————————————————
class SmartAxisSystem:
    def __init__(self, screen_width, screen_height, margin=80):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.margin = margin  # 边距，用于显示坐标刻度
        
        # 绘图区域（去掉边距后的实际绘图区）
        self.plot_x = margin
        self.plot_y = margin
        self.plot_width = screen_width - 2 * margin
        self.plot_height = screen_height - 2 * margin
        
        # 动态缩放参数
        self.auto_zoom = True
        self.zoom_speed = 0.2

        # 平滑度参数
        self.base_smoothness = 0.05  # 基础平滑度
        self.max_smoothness = 0.75   # 最大平滑度（紧急追赶）
        
        # 坐标轴显示参数
        self.grid_spacing = 50  # 网格间距（像素）
        self.show_grid = True
        
    def update_viewport(self, points):
        """根据数据点自动调整视图范围和缩放"""
        if len(points) < 2:
            return 1.0, 0.0, 0.0  # zoom, offset_x, offset_y
        
        # 提取所有点的坐标
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        # 计算数据范围
        x_min, x_max = min(x_coords) - 1, max(x_coords) + 1
        y_min, y_max = min(y_coords) - 1, max(y_coords) + 1
        
        # 避免除零
        data_width = max(x_max - x_min, 0.1)
        data_height = max(y_max - y_min, 0.1)
        
        # 计算最佳缩放比例（让数据适应绘图区域）
        zoom_x = self.plot_width / data_width
        zoom_y = self.plot_height / data_height
        optimal_zoom = min(zoom_x, zoom_y) * 0.8  # 留20%边距
        
        # (可选)限制缩放范围
        # optimal_zoom = max(5.0, min(optimal_zoom, 200.0))
        
        # 计算视图中心（数据边界中心）
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        
        # 计算偏移量（让数据居中）
        offset_x = self.plot_x + self.plot_width/2 - center_x * optimal_zoom
        offset_y = self.plot_y + self.plot_height/2 - center_y * optimal_zoom
        
        return optimal_zoom, offset_x, offset_y
    
    def world_to_screen(self, world_x, world_y, zoom, offset_x, offset_y):
        """世界坐标转屏幕坐标"""
        screen_x = int(world_x * zoom + offset_x)
        screen_y = int(world_y * zoom + offset_y)
        return screen_x, screen_y
    
    def draw_axes(self, screen, zoom, offset_x, offset_y):
        """绘制坐标轴和网格"""
        # 绘制外边框
        pygame.draw.rect(screen, AXIS_COLOR, (self.plot_x, self.plot_y, self.plot_width, self.plot_height), 2)
        
        if not self.show_grid:
            return
            
        # 计算网格线的世界坐标间隔（保持屏幕间距大致恒定）
        world_spacing = self.grid_spacing / zoom
        
        # 找到最近的"整齐"的网格间隔
        magnitude = 10 ** math.floor(math.log10(world_spacing))
        grid_step = round(world_spacing / magnitude) * magnitude
        
        if grid_step < 0.1:  # 避免网格过密
            grid_step = 0.1
        
        # 计算网格起点（对齐到整齐的数值）
        origin_x, origin_y = self.world_to_screen(0, 0, zoom, offset_x, offset_y)
        
        # 绘制网格线
        font = load_font(font = "./global.ttf", size = 14)
        
        # 水平网格线
        y = math.ceil(-offset_y / zoom / grid_step) * grid_step
        while True:
            screen_y = int(y * zoom + offset_y)
            if screen_y < self.plot_y:
                y += grid_step
                continue
            if screen_y > self.plot_y + self.plot_height:
                break
                
            if abs(y) > 0.001:  # 非零线用虚线
                for x in range(self.plot_x, self.plot_x + self.plot_width, 4):
                    if x % 8 < 4:
                        pygame.draw.line(screen, GRID_COLOR, (x, screen_y), (x+2, screen_y), 1)
            else:  # 零线用实线
                pygame.draw.line(screen, AXIS_COLOR, 
                               (self.plot_x, screen_y), 
                               (self.plot_x + self.plot_width, screen_y), 1)
            
            # 绘制Y轴刻度标签
            if self.plot_x - 30 > 0:
                label = font.render(f"{y:.1f}" if grid_step < 10 else f"{y:.0f}", True, TEXT_COLOR)
                screen.blit(label, (self.plot_x - 44, screen_y - 10))
            
            y += grid_step
        
        # 垂直网格线（类似逻辑）
        x = math.ceil(-offset_x / zoom / grid_step) * grid_step
        while True:
            screen_x = int(x * zoom + offset_x)
            if screen_x < self.plot_x:
                x += grid_step
                continue
            if screen_x > self.plot_x + self.plot_width:
                break
                
            if abs(x) > 0.001:
                for y in range(self.plot_y, self.plot_y + self.plot_height, 4):
                    if y % 8 < 4:
                        pygame.draw.line(screen, GRID_COLOR, 
                                        (screen_x, y), (screen_x, y+2), 1)
            else:
                pygame.draw.line(screen, AXIS_COLOR, 
                               (screen_x, self.plot_y), 
                               (screen_x, self.plot_y + self.plot_height), 1)
            
            if self.plot_y - 30 > 0:
                label = font.render(f"{x:.1f}" if grid_step < 10 else f"{x:.0f}", True, TEXT_COLOR)
                screen.blit(label, (screen_x - 15, self.plot_y - 30))
            
            x += grid_step
        
        # 绘制原点标记
        if (self.plot_x <= origin_x <= self.plot_x + self.plot_width and 
            self.plot_y <= origin_y <= self.plot_y + self.plot_height):
            pygame.draw.circle(screen, AXIS_COLOR, (origin_x, origin_y), 3)
            origin_label = font.render("(0,0)", True, TEXT_COLOR)
            screen.blit(origin_label, (origin_x + 5, origin_y + 5))

# --------------------------------
# 绘制障碍物
# --------------------------------
def draw_buildings(screen, axis: SmartAxisSystem, zoom, offset_x, offset_y, L, D):
    if L <= 0:
        return

    period = L + D

    # 当前可见世界范围
    left = (-offset_x) / zoom
    right = (axis.plot_width - offset_x) / zoom
    bottom = (-offset_y) / zoom
    top = (axis.plot_height - offset_y) / zoom

    ix_min = int(math.floor(left / period)) - 1
    ix_max = int(math.ceil(right / period)) + 1
    iy_min = int(math.floor(bottom / period)) - 1
    iy_max = int(math.ceil(top / period)) + 1

    color = (255, 220, 80)  # 黄色

    for ix in range(ix_min, ix_max):
        for iy in range(iy_min, iy_max):
            bx = ix * period + D / 2
            by = iy * period + D / 2

            x0, y0 = axis.world_to_screen(bx, by, zoom, offset_x, offset_y)
            x1, y1 = axis.world_to_screen(bx + L, by + L, zoom, offset_x, offset_y)

            if x1 < axis.plot_x or y1 < axis.plot_y:
                continue
            if x0 > axis.plot_x + axis.plot_width or y0 > axis.plot_y + axis.plot_height:
                continue

            if x1 > axis.plot_x + axis.plot_width:
                x1 = axis.plot_x + axis.plot_width
            if x0 < axis.plot_x:
                x0 = axis.plot_x
            if y1 > axis.plot_y + axis.plot_height:
                y1 = axis.plot_y + axis.plot_height
            if y0 < axis.plot_y:
                y0 = axis.plot_y

            rect = pygame.Rect(
                min(x0, x1),
                min(y0, y1),
                abs(x1 - x0),
                abs(y1 - y0),
            )

            pygame.draw.rect(screen, color, rect, 2)


# --------------------------------
# 空气墙
# --------------------------------
def hit_air_wall(x, y, wx, wy):
    if wx is None or wy is None:
        return False
    return not (-wx <= x <= wx and -wy <= y <= wy)

# --------------------------------
# 障碍物检测
# --------------------------------
def in_building(x, y, L, D):
    if L <= 0:
        return False

    period = L + D
    xm = abs(x) % period
    ym = abs(y) % period

    street_half = D / 2

    return (
        street_half < xm < street_half + L and
        street_half < ym < street_half + L
    )


# ————————————————————————————————
# 初始化系统和状态
# ————————————————————————————————
axis_system = SmartAxisSystem(WIDTH, HEIGHT)

# 智能体状态
x, y = 0.0, 0.0
theta = np.random.uniform(0, 2 * math.pi)
points = deque(maxlen = MAX_POINTS)
points.append((x, y))

step_count = 0
total_distance = 0
running = True

# 视图参数
zoom = SCALE
offset_x = WIDTH // 2
offset_y = HEIGHT // 2

# ————————————————————————————————
# 主循环
# ————————————————————————————————
timer.start()
while running:
    # 事件处理
    for event in pygame.event.get():
        if apply_btn.clicked(event):
            # 重置
            try:
                params["L_MEAN"] = float(inputs["L_MEAN"].text)
                params["EPSILON"] = float(inputs["EPSILON"].text)
                params["DELTA"] = float(inputs["DELTA"].text) * math.pi / 180
                params["TEMPO"] = float(inputs["TEMPO"].text)
                params["MAX_POINTS"] = int(inputs["MAX_POINTS"].text)

                L_MEAN = params["L_MEAN"]
                EPSILON = params["EPSILON"]
                DELTA = params["DELTA"]
                MAX_POINTS = params["MAX_POINTS"]
                TEMPO = params["TEMPO"]

                def parse_or_none(txt):
                    return None if txt.strip() == "" else float(txt)

                AIR_WALL_X = parse_or_none(inputs["AIR_WALL_X"].text)
                AIR_WALL_Y = parse_or_none(inputs["AIR_WALL_Y"].text)
                BUILDING_L = float(inputs["BUILDING_L"].text)
                STREET_D = float(inputs["STREET_D"].text)
                params["TURN_ANGLE"] = parse_or_none(inputs["TURN_ANGLE"].text)

                x, y, total_distance = 0, 0, 0
                theta = np.random.uniform(0, 2 * math.pi)
                step_count = 0
                timer.reset()
                period = 60000 / params["TEMPO"] # ms
                points = deque(points, maxlen = MAX_POINTS)
                points.clear()
                points.append((x, y))
                timer.start()
            except:
                print("Invalid parameter.")
                inputs = {
                    "L_MEAN": TextInput(ui_x, 120, UI_WIDTH, 30, L_MEAN),
                    "EPSILON": TextInput(ui_x, 200, UI_WIDTH, 30, EPSILON),
                    "DELTA": TextInput(ui_x, 280, UI_WIDTH, 30, round(DELTA * 180 / math.pi, 2)),
                    "TEMPO": TextInput(ui_x, 360, UI_WIDTH, 30, TEMPO),
                    "MAX_POINTS": TextInput(ui_x, 440, UI_WIDTH, 30, MAX_POINTS),
                    "AIR_WALL_X": TextInput(ui_x, 520, UI_WIDTH, 30, ""),
                    "AIR_WALL_Y": TextInput(ui_x, 600, UI_WIDTH, 30, ""),
                    "BUILDING_L": TextInput(ui_x, 680, UI_WIDTH, 30, "0"),
                    "STREET_D": TextInput(ui_x, 760, UI_WIDTH, 30, "0"),
                    "TURN_ANGLE": TextInput(ui_x, 840, UI_WIDTH, 30, ""),
                }
        elif mesh_btn.clicked(event):
            axis_system.show_grid = not axis_system.show_grid
            mesh_btn.label = "Mesh: Off" if not axis_system.show_grid else "Mesh: On"
        elif zoom_btn.clicked(event):
            axis_system.auto_zoom = not axis_system.auto_zoom
            zoom_btn.label = "Auto Zoom: Off" if not axis_system.auto_zoom else "Auto Zoom: On"
        elif reset_btn.clicked(event):
            # 重置
            x, y, total_distance = 0, 0, 0
            theta = np.random.uniform(0, 2 * math.pi)
            points.clear()
            points = deque(points, maxlen = MAX_POINTS)
            points.append((x, y))
            step_count = 0
            inputs = {
                "L_MEAN": TextInput(ui_x, 120, UI_WIDTH, 30, default["L_MEAN"]),
                "EPSILON": TextInput(ui_x, 200, UI_WIDTH, 30, default["EPSILON"]),
                "DELTA": TextInput(ui_x, 280, UI_WIDTH, 30, round(default["DELTA"] * 180 / math.pi, 2)),
                "TEMPO": TextInput(ui_x, 360, UI_WIDTH, 30, default["TEMPO"]),
                "MAX_POINTS": TextInput(ui_x, 440, UI_WIDTH, 30, default["MAX_POINTS"]),
                "AIR_WALL_X": TextInput(ui_x, 520, UI_WIDTH, 30, ""),
                "AIR_WALL_Y": TextInput(ui_x, 600, UI_WIDTH, 30, ""),
                "BUILDING_L": TextInput(ui_x, 680, UI_WIDTH, 30, default["BUILDING_L"]),
                "STREET_D": TextInput(ui_x, 760, UI_WIDTH, 30, default["STREET_D"]),
                "TURN_ANGLE": TextInput(ui_x, 840, UI_WIDTH, 30, ""),
            }
            try:
                params["L_MEAN"] = float(inputs["L_MEAN"].text)
                params["EPSILON"] = float(inputs["EPSILON"].text)
                params["DELTA"] = float(inputs["DELTA"].text) * math.pi / 180
                params["TEMPO"] = float(inputs["TEMPO"].text)
                params["MAX_POINTS"] = int(inputs["MAX_POINTS"].text)
                params["TURN_ANGLE"] = ""

                L_MEAN = params["L_MEAN"]
                EPSILON = params["EPSILON"]
                DELTA = params["DELTA"]
                MAX_POINTS = params["MAX_POINTS"]
                TEMPO = params["TEMPO"]

                period = 60000 / params["TEMPO"] # ms
                points = deque(points, maxlen = MAX_POINTS)
                points.clear()
                points.append((x, y))
                timer.reset()
                timer.start()
            except:
                print("Invalid parameter.")
                inputs = {
                    "L_MEAN": TextInput(ui_x, 120, UI_WIDTH, 30, L_MEAN),
                    "EPSILON": TextInput(ui_x, 200, UI_WIDTH, 30, EPSILON),
                    "DELTA": TextInput(ui_x, 280, UI_WIDTH, 30, round(DELTA * 180 / math.pi, 2)),
                    "TEMPO": TextInput(ui_x, 360, UI_WIDTH, 30, TEMPO),
                    "MAX_POINTS": TextInput(ui_x, 440, UI_WIDTH, 30, MAX_POINTS),
                    "TURN_ANGLE": TextInput(ui_x, 840, UI_WIDTH, 30, ""),
                }
        elif sound_btn.clicked(event):
            sound_btn.label = "Sound: Off" if not sound_btn.label == "Sound: Off" else "Sound: On"
            sound_on = not sound_on
        elif event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
            elif event.key == pygame.K_SPACE:
                # 重置
                x, y = 0, 0
                theta = np.random.uniform(0, 2 * math.pi)
                points.clear()
                points.append((x, y))
                step_count = 0
                inputs = {
                    "L_MEAN": TextInput(ui_x, 120, UI_WIDTH, 30, default["L_MEAN"]),
                    "EPSILON": TextInput(ui_x, 200, UI_WIDTH, 30, default["EPSILON"]),
                    "DELTA": TextInput(ui_x, 280, UI_WIDTH, 30, round(default["DELTA"] * 180 / math.pi, 2)),
                    "TEMPO": TextInput(ui_x, 360, UI_WIDTH, 30, default["TEMPO"]),
                    "MAX_POINTS": TextInput(ui_x, 440, UI_WIDTH, 30, default["MAX_POINTS"]),
                    "AIR_WALL_X": TextInput(ui_x, 520, UI_WIDTH, 30, ""),
                    "AIR_WALL_Y": TextInput(ui_x, 600, UI_WIDTH, 30, ""),
                    "BUILDING_L": TextInput(ui_x, 680, UI_WIDTH, 30, default["BUILDING_L"]),
                    "STREET_D": TextInput(ui_x, 760, UI_WIDTH, 30, default["STREET_D"]),
                    "TURN_ANGLE": TextInput(ui_x, 840, UI_WIDTH, 30, ""),
                }
            elif event.key == pygame.K_g:
                axis_system.show_grid = not axis_system.show_grid
            elif event.key == pygame.K_a:
                axis_system.auto_zoom = not axis_system.auto_zoom
        elif event.type == pygame.MOUSEWHEEL:
            # 手动缩放（仅在自动缩放关闭时有效）
            if not axis_system.auto_zoom:
                zoom *= 1.1 if event.y > 0 else 0.9
                zoom = max(5.0, min(zoom, 200.0))
        for inp in inputs.values():
            inp.handle_event(event)

    if timer.get_elapsed_time() >= period * step_count:
    
        # —— 每步移动 ——
        L = np.random.uniform(L_MEAN - EPSILON, L_MEAN + EPSILON)
        d_theta = np.random.uniform(-DELTA, DELTA)
        theta += d_theta

        x_next = x + L * math.cos(theta)
        y_next = y + L * math.sin(theta)

        # —— 空气墙 ——
        if hit_air_wall(x_next, y_next, AIR_WALL_X, AIR_WALL_Y):
            theta = (theta + math.pi) % (2 * math.pi)
            x_next, y_next = x, y

        # —— 建筑块 ——
        elif in_building(x_next, y_next, BUILDING_L, STREET_D):
            # theta = np.random.uniform(0, 2 * math.pi)
            # 向右转
            if params["TURN_ANGLE"] == None:
                theta = np.random.uniform(0, 2 * math.pi)
            else:
                theta = (theta + float(params["TURN_ANGLE"]) * math.pi / 180) % (2 * math.pi)
            x_next, y_next = x, y

        sx, sy = axis_system.world_to_screen(x_next, y_next, zoom, offset_x, offset_y)
        out_of_view = not (
            axis_system.plot_x <= sx <= axis_system.plot_x + axis_system.plot_width and
            axis_system.plot_y <= sy <= axis_system.plot_y + axis_system.plot_height
        )

        if out_of_view and axis_system.auto_zoom:
            # 临时把“预测点”加入历史
            temp_points = list(points) + [(x_next, y_next)]
        
            new_zoom, new_offset_x, new_offset_y = axis_system.update_viewport(temp_points)
        
            # 这里可以选择：
            # A. 立刻跳变（强制重构）
            zoom = new_zoom
            offset_x = new_offset_x
            offset_y = new_offset_y

        x,y = x_next, y_next
        points.append((x, y))
        total_distance += L
        step_count += 1
        if sound_on:
            if step_count % 16 == 1:
                sound_cymbal.play()
            if step_count % 2 == 0:
                sound_snare.play()
            if step_count % 2 == 1:
                sound_kick.play()
    
        # —— 智能视图调整 ——
        if axis_system.auto_zoom and len(points) > 1:
            new_zoom, new_offset_x, new_offset_y = axis_system.update_viewport(points)
            # 平滑过渡
            zoom += (new_zoom - zoom) * axis_system.zoom_speed
            offset_x += (new_offset_x - offset_x) * axis_system.zoom_speed
            offset_y += (new_offset_y - offset_y) * axis_system.zoom_speed
    
        # —— 清屏和绘制 ——
        screen.fill(BACKGROUND)
    
        # 绘制坐标轴系统
        axis_system.draw_axes(screen, zoom, offset_x, offset_y)

        # —— 建筑物（黄色） ——
        draw_buildings(screen, axis_system, zoom, offset_x, offset_y, BUILDING_L, STREET_D)
    
        # 绘制轨迹（渐变效果）
        if len(points) > 1:
            screen_points = []
            for px, py in points:
                sx, sy = axis_system.world_to_screen(px, py, zoom, offset_x, offset_y)
                screen_points.append((sx, sy))
        
            # 渐变线段
            n = len(screen_points)
            r, g, b, a = 100, 200, 255, 255
            for i in range(n, 1, -1):
                # 颜色插值：从旧到新，蓝色渐变
                t = 1 - i / MAX_POINTS
                r = int(32 + t * 68)
                g = int(32 + t * 168)
                b = int(32 + t * 223)
                pygame.draw.line(screen, (r, g, b), screen_points[-i], screen_points[-i + 1], 2)
    
        # 绘制智能体
        agent_x, agent_y = axis_system.world_to_screen(x, y, zoom, offset_x, offset_y)
        pygame.draw.circle(screen, AGENT_COLOR, (agent_x, agent_y), 6)
    
        # 方向指示
        dx = math.cos(theta) * 12
        dy = math.sin(theta) * 12
        pygame.draw.line(screen, (255, 255, 200), 
                        (agent_x, agent_y), 
                        (agent_x + dx, agent_y + dy), 3)
    
        # —— HUD 信息 ——
        
        hud = pygame.Surface((380, 185), pygame.SRCALPHA)
        hud.fill((64, 64, 64, 140))
        info_lines = [
            f"Steps: {step_count}",
            f"Time: {timer.get_formatted_time()}",
            f"Position: ({x:.2f}, {y:.2f}) m",
            f"Displacement from (0,0): {math.hypot(x, y):.2f} m",
            f"Total distance: {total_distance:.2f} m",
            f"Zoom: {zoom:.2f} px/m",
        ]
    
        for i, line in enumerate(info_lines):
            text = font.render(line, True, TEXT_COLOR)
            hud.blit(text, (10, 10 + i * 28))
        screen.blit(hud, (100, 100))

        panel = pygame.Surface((PANEL_WIDTH, HEIGHT))
        panel.fill((40, 40, 40))
        screen.blit(panel, (PLOT_WIDTH, 0))

        title = title_font.render("Control Panel", True, TEXT_COLOR)
        screen.blit(title, (ui_x, 35))

        labels = [
            ("Average step length (m)", "L_MEAN"),
            ("Step length fluctuate ± (m)", "EPSILON"),
            ("Maximum direction-change angle ± (degree)", "DELTA"),
            ("Step per minute (aka. Tempo) ", "TEMPO"),
            ("Locus length (points)", "MAX_POINTS"),
            ("Air wall half-width X (m) (blank = no wall)", "AIR_WALL_X"),
            ("Air wall half-height Y (m) (blank = no wall)", "AIR_WALL_Y"),
            ("Building size L (m) (0 = no building)", "BUILDING_L"),
            ("Street width D (m) (ignore if L=0)", "STREET_D"),
            ("Turn angle (degree) (blank = random)", "TURN_ANGLE"),
        ]

        for i, (label, key) in enumerate(labels):
            text = ui_font.render(label, True, TEXT_COLOR)
            screen.blit(text, (ui_x, 90 + i * 80))
            inputs[key].draw(screen, ui_font)

        apply_btn.draw(screen, ui_font)
        mesh_btn.draw(screen, ui_font)
        reset_btn.draw(screen, ui_font)
        zoom_btn.draw(screen, ui_font)
        sound_btn.draw(screen, ui_font)

    # 更新显示
    pygame.display.flip()
    clock.tick(60) 


pygame.quit()
sys.exit()