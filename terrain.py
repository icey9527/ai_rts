import pygame
import random
import math
from config import *

class TerrainObject:
    def __init__(self, x, y, terrain_type, radius, **kwargs):
        self.x = x
        self.y = y
        self.terrain_type = terrain_type
        self.radius = radius
        self.color = self.get_color()
        self.destructible = kwargs.get('destructible', False)
        self.hp = kwargs.get('hp', 100) if self.destructible else 0
        self.max_hp = self.hp
        
    def get_color(self):
        if self.terrain_type == TerrainType.ASTEROID:
            return (120, 120, 120)
        elif self.terrain_type == TerrainType.DEBRIS:
            return (80, 80, 80)
        elif self.terrain_type == TerrainType.BARRIER:
            return (60, 60, 150)
        elif self.terrain_type == TerrainType.CRYSTAL:
            return (150, 100, 255)
        return COLOR_GRAY
        
    def blocks_movement(self):
        return self.terrain_type in [TerrainType.ASTEROID, TerrainType.DEBRIS, TerrainType.BARRIER]
        
    def take_damage(self, damage):
        """对可破坏地形造成伤害"""
        if self.destructible and self.hp > 0:
            self.hp -= damage
            return self.hp <= 0  # 返回是否被摧毁
        return False
        
    def draw(self, screen, camera):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        radius = int(self.radius * camera.zoom)
        
        if radius > 0:
            # 基础颜色
            color = self.color
            
            # 如果是可破坏的，根据血量调整颜色
            if self.destructible and self.hp < self.max_hp:
                damage_ratio = 1 - (self.hp / self.max_hp)
                color = (
                    min(255, color[0] + int(100 * damage_ratio)),
                    max(50, color[1] - int(50 * damage_ratio)),
                    max(50, color[2] - int(50 * damage_ratio))
                )
            
            # 绘制不同类型的地形
            if self.terrain_type == TerrainType.CRYSTAL:
                # 水晶 - 钻石形状
                points = []
                for i in range(6):
                    angle = i * math.pi / 3
                    px = screen_x + math.cos(angle) * radius
                    py = screen_y + math.sin(angle) * radius
                    points.append((px, py))
                pygame.draw.polygon(screen, color, points)
                pygame.draw.polygon(screen, COLOR_WHITE, points, 2)
            elif self.terrain_type == TerrainType.BARRIER:
                # 能量屏障 - 方形
                rect = pygame.Rect(screen_x - radius, screen_y - radius, radius * 2, radius * 2)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, COLOR_CYAN, rect, 2)
            else:
                # 小行星和碎片 - 圆形
                pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
                pygame.draw.circle(screen, COLOR_WHITE, (screen_x, screen_y), radius, 1)
                
            # 绘制血量条（如果是可破坏的且受损）
            if self.destructible and self.hp < self.max_hp:
                bar_width = radius * 2
                bar_height = 4
                bar_x = screen_x - bar_width // 2
                bar_y = screen_y - radius - 10
                
                hp_ratio = self.hp / self.max_hp
                pygame.draw.rect(screen, COLOR_ENEMY, (bar_x, bar_y, bar_width, bar_height))
                pygame.draw.rect(screen, COLOR_PLAYER, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))

class TerrainManager:
    def __init__(self):
        self.terrain_objects = []
        self.generate_terrain()
        
    def generate_terrain(self):
        """生成随机地形"""
        self.terrain_objects = []
        
        # 生成小行星带
        for _ in range(12):
            x = random.randint(300, MAP_WIDTH - 300)
            y = random.randint(300, MAP_HEIGHT - 300)
            radius = random.randint(40, 90)
            
            # 确保不会生成在玩家或敌人基地附近
            if (400 < y < MAP_HEIGHT - 400):
                terrain = TerrainObject(x, y, TerrainType.ASTEROID, radius, 
                                      destructible=True, hp=150)
                self.terrain_objects.append(terrain)
        
        # 生成碎片
        for _ in range(20):
            x = random.randint(200, MAP_WIDTH - 200)
            y = random.randint(200, MAP_HEIGHT - 200)
            radius = random.randint(20, 40)
            
            if (350 < y < MAP_HEIGHT - 350):
                terrain = TerrainObject(x, y, TerrainType.DEBRIS, radius)
                self.terrain_objects.append(terrain)
                
        # 生成能量屏障
        for _ in range(6):
            x = random.randint(400, MAP_WIDTH - 400)
            y = random.randint(500, MAP_HEIGHT - 500)
            radius = random.randint(30, 60)
            
            terrain = TerrainObject(x, y, TerrainType.BARRIER, radius,
                                  destructible=True, hp=200)
            self.terrain_objects.append(terrain)
            
        # 生成水晶
        for _ in range(8):
            x = random.randint(300, MAP_WIDTH - 300)
            y = random.randint(400, MAP_HEIGHT - 400)
            radius = random.randint(25, 45)
            
            terrain = TerrainObject(x, y, TerrainType.CRYSTAL, radius)
            self.terrain_objects.append(terrain)
                
    def is_position_blocked(self, x, y, unit_radius=0):
        """检查位置是否被地形阻挡"""
        for terrain in self.terrain_objects:
            if terrain.blocks_movement():
                distance = math.sqrt((x - terrain.x)**2 + (y - terrain.y)**2)
                if distance < terrain.radius + unit_radius:
                    return True
        return False
        
    def find_clear_path(self, start_x, start_y, end_x, end_y, unit_radius=0):
        """简单的路径查找，避开障碍物"""
        # 检查直线路径是否畅通
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            check_x = start_x + (end_x - start_x) * t
            check_y = start_y + (end_y - start_y) * t
            
            if self.is_position_blocked(check_x, check_y, unit_radius):
                # 如果路径被阻挡，尝试绕行
                return self.find_detour(start_x, start_y, end_x, end_y, unit_radius)
                
        return [(end_x, end_y)]  # 直线路径畅通
        
    def find_detour(self, start_x, start_y, end_x, end_y, unit_radius=0):
        """寻找绕行路径"""
        # 尝试多个绕行点
        mid_x = (start_x + end_x) / 2
        mid_y = (start_y + end_y) / 2
        
        # 尝试不同的偏移方向和距离
        for distance in [80, 150, 250]:
            for angle_offset in [math.pi/2, -math.pi/2, math.pi/4, -math.pi/4]:
                test_x = mid_x + math.cos(angle_offset) * distance
                test_y = mid_y + math.sin(angle_offset) * distance
                
                if not self.is_position_blocked(test_x, test_y, unit_radius):
                    return [(test_x, test_y), (end_x, end_y)]
                
        return [(end_x, end_y)]  # 如果绕行失败，还是直线前进
        
    def damage_terrain_at(self, x, y, damage, radius=50):
        """对指定位置的地形造成伤害"""
        destroyed = []
        for terrain in self.terrain_objects[:]:  # 使用切片复制避免修改时出错
            distance = math.sqrt((terrain.x - x)**2 + (terrain.y - y)**2)
            if distance <= radius and terrain.destructible:
                if terrain.take_damage(damage):
                    destroyed.append(terrain)
                    self.terrain_objects.remove(terrain)
        return destroyed
        
    def draw(self, screen, camera):
        for terrain in self.terrain_objects:
            terrain.draw(screen, camera)