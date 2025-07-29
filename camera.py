import pygame
from config import EDGE_SCROLL_MARGIN, EDGE_SCROLL_SPEED, MAP_WIDTH, MAP_HEIGHT

class Camera:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 2.0
        self.drag_start = None
        self.follow_target = None
        self.follow_speed = 0.1  # 跟随速度
        self.edge_scroll_enabled = False  # 边缘滚动开关
        
        # 地图边界
        self.map_min_x = -200
        self.map_max_x = MAP_WIDTH + 200
        self.map_min_y = -200
        self.map_max_y = MAP_HEIGHT + 200
        
    def world_to_screen(self, x, y):
        """将世界坐标转换为屏幕坐标"""
        screen_x = (x - self.x) * self.zoom + self.width // 2
        screen_y = (y - self.y) * self.zoom + self.height // 2
        return int(screen_x), int(screen_y)
        
    def screen_to_world(self, screen_x, screen_y):
        """将屏幕坐标转换为世界坐标"""
        world_x = (screen_x - self.width // 2) / self.zoom + self.x
        world_y = (screen_y - self.height // 2) / self.zoom + self.y
        return world_x, world_y
        
    def set_follow_target(self, target):
        """设置跟随目标"""
        self.follow_target = target
        
    def stop_following(self):
        """停止跟随"""
        self.follow_target = None
        
    def enable_edge_scroll(self, enable=True):
        """启用/禁用边缘滚动"""
        self.edge_scroll_enabled = enable
        
    def clamp_position(self):
        """限制相机位置在地图范围内"""
        # 计算可视范围
        half_view_width = (self.width / 2) / self.zoom
        half_view_height = (self.height / 2) / self.zoom
        
        # 限制相机位置，确保可以看到地图边缘
        min_x = self.map_min_x + half_view_width
        max_x = self.map_max_x - half_view_width
        min_y = self.map_min_y + half_view_height
        max_y = self.map_max_y - half_view_height
        
        self.x = max(min_x, min(max_x, self.x))
        self.y = max(min_y, min(max_y, self.y))
        
    def update(self, keys, mouse_buttons, mouse_pos, dt=1/60):
        # 跟随目标
        if self.follow_target:
            target_x = self.follow_target.x if hasattr(self.follow_target, 'x') else self.follow_target[0]
            target_y = self.follow_target.y if hasattr(self.follow_target, 'y') else self.follow_target[1]
            
            # 平滑跟随
            dx = target_x - self.x
            dy = target_y - self.y
            self.x += dx * self.follow_speed
            self.y += dy * self.follow_speed
            
            # 如果距离很近就停止跟随微调
            if abs(dx) < 1 and abs(dy) < 1:
                self.x = target_x
                self.y = target_y
        
        # 边缘滚动（只在启用时工作）
        if self.edge_scroll_enabled:
            self.update_edge_scroll(mouse_pos, dt)
        
        # 鼠标中键拖动（会停止跟随）
        if mouse_buttons[1]:  # 中键
            if self.drag_start:
                dx = (mouse_pos[0] - self.drag_start[0]) / self.zoom
                dy = (mouse_pos[1] - self.drag_start[1]) / self.zoom
                self.x -= dx
                self.y -= dy
                self.stop_following()  # 手动拖动时停止跟随
            self.drag_start = mouse_pos
        else:
            self.drag_start = None
            
        # 键盘控制（也会停止跟随）
        move_speed = 300 * dt / self.zoom  # 更快的键盘移动速度
        moved = False
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= move_speed
            moved = True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += move_speed
            moved = True
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= move_speed
            moved = True
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += move_speed
            moved = True
            
        if moved:
            self.stop_following()
            
        # 限制相机位置
        self.clamp_position()
            
    def update_edge_scroll(self, mouse_pos, dt):
        """边缘滚动更新"""
        scroll_speed = EDGE_SCROLL_SPEED * dt / self.zoom
        moved = False
        
        # 左边缘
        if mouse_pos[0] < EDGE_SCROLL_MARGIN:
            self.x -= scroll_speed
            moved = True
            
        # 右边缘
        elif mouse_pos[0] > self.width - EDGE_SCROLL_MARGIN:
            self.x += scroll_speed
            moved = True
            
        # 上边缘
        if mouse_pos[1] < EDGE_SCROLL_MARGIN:
            self.y -= scroll_speed
            moved = True
            
        # 下边缘
        elif mouse_pos[1] > self.height - EDGE_SCROLL_MARGIN:
            self.y += scroll_speed
            moved = True
            
        # 边缘滚动时停止跟随
        if moved:
            self.stop_following()
            
    def zoom_in(self):
        self.zoom = min(self.zoom * 1.1, self.max_zoom)
        self.clamp_position()
        
    def zoom_out(self):
        self.zoom = max(self.zoom / 1.1, self.min_zoom)
        self.clamp_position()
        
    def focus_on(self, x, y):
        """立即聚焦到指定位置"""
        self.x = x
        self.y = y
        self.stop_following()
        self.clamp_position()