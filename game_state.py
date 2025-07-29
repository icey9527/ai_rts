import pygame
import random
import math
from ai import SimpleAI
from config import COLOR_BLACK, COLOR_WHITE, COLOR_YELLOW
from terrain import TerrainManager
from improved_ai import AdvancedAI, HyperAggressiveAI, TurtleAI

class GameState:
    def __init__(self):
        self.units = []
        self.effects = []
        self.projectiles = []
        self.selected_units = []
        self.player_team = 0
        self.ai_controllers = []
        self.level_time = 0
        self.background_image = None
        self.stars = []
        self.terrain_manager = TerrainManager()
        self.game_paused = False  # 统一的暂停状态
        self.generate_starfield()
        
    def generate_starfield(self):
        """生成星空背景"""
        self.stars = []
        for _ in range(300):
            x = random.randint(-3000, 3000)
            y = random.randint(-3000, 3000)
            brightness = random.randint(50, 255)
            size = random.randint(1, 3)
            self.stars.append({
                'x': x, 'y': y, 
                'brightness': brightness, 
                'size': size,
                'color': (brightness, brightness, brightness)
            })
        
    def add_unit(self, unit):
        self.units.append(unit)
        
    def add_effect(self, effect):
        self.effects.append(effect)
        
    def add_projectile(self, projectile):
        """添加投射物"""
        self.projectiles.append(projectile)
        
    def get_all_friendly_units(self, team):
        """获取指定阵营的所有单位（除了母舰）- 修复：包含修理机"""
        from units import UnitType, UnitState
        return [u for u in self.units 
                if (u.team == team and 
                    u.unit_type != UnitType.MOTHERSHIP and 
                    u.state != UnitState.DEAD)]
        
    def get_mothership(self, team):
        """获取指定阵营的母舰"""
        from units import UnitType, UnitState
        for unit in self.units:
            if (unit.team == team and 
                unit.unit_type == UnitType.MOTHERSHIP and 
                unit.state != UnitState.DEAD):
                return unit
        return None
        
    def get_units_by_team(self, team):
        """获取指定阵营的所有存活单位"""
        from units import UnitState
        return [u for u in self.units if u.team == team and u.state != UnitState.DEAD]
        
    def get_enemy_units(self, team):
        """获取敌方单位"""
        from units import UnitState
        return [u for u in self.units if u.team != team and u.state != UnitState.DEAD]
        
    def pause_game(self):
        """暂停游戏"""
        self.game_paused = True
        print(f"Game paused: {self.game_paused}")  # 调试信息
        
    def resume_game(self):
        """恢复游戏"""
        self.game_paused = False
        print(f"Game resumed: {self.game_paused}")  # 调试信息
        
    def is_paused(self):
        """检查游戏是否暂停"""
        return self.game_paused
        
    def clear_selection(self):
        """清除所有选择"""
        for unit in self.units:
            unit.selected = False
        self.selected_units.clear()
        
    def select_unit(self, unit):
        """选择单位（包括敌方单位）"""
        self.clear_selection()
        unit.selected = True
        if unit.team == self.player_team:
            self.selected_units.append(unit)
            
    def select_units_in_area(self, min_x, min_y, max_x, max_y):
        """选择区域内的友方单位"""
        self.clear_selection()
        for unit in self.units:
            if (unit.team == self.player_team and 
                min_x <= unit.x <= max_x and 
                min_y <= unit.y <= max_y):
                unit.selected = True
                self.selected_units.append(unit)
                
    def get_unit_at_position(self, x, y, radius=None):
        """获取指定位置的单位"""
        for unit in self.units:
            from units import UnitState
            if unit.state == UnitState.DEAD:
                continue
                
            distance = math.sqrt((unit.x - x)**2 + (unit.y - y)**2)
            check_radius = radius if radius else unit.radius
            if distance <= check_radius:
                return unit
        return None
        
    def find_nearest_enemy(self, unit, max_range=None):
        """查找最近的敌方单位"""
        enemies = self.get_enemy_units(unit.team)
        if not enemies:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for enemy in enemies:
            distance = unit.distance_to(enemy)
            if max_range and distance > max_range:
                continue
            if distance < min_distance:
                min_distance = distance
                nearest = enemy
                
        return nearest
        
    def find_damaged_allies(self, unit, max_range=None):
        """查找受损的友方单位"""
        allies = self.get_units_by_team(unit.team)
        damaged = []
        
        for ally in allies:
            if ally == unit or ally.hp >= ally.max_hp:
                continue
                
            distance = unit.distance_to(ally)
            if max_range and distance > max_range:
                continue
                
            damaged.append(ally)
            
        # 按受损程度排序，最严重的在前
        damaged.sort(key=lambda u: u.hp / u.max_hp)
        return damaged
        
    def update(self, dt):
        """更新游戏状态"""
        # 只有在非暂停状态下才更新
        if self.is_paused():
            return
        
        if not self.is_paused():
            self.level_time += dt
            
        # 更新单位
        for unit in self.units:
            unit.update(dt, self.units, self)
            
        # 更新投射物
        self.projectiles = [p for p in self.projectiles if p.update(dt, self.units, self)]
            
        # 移除死亡单位
        from units import UnitState
        dead_units = [u for u in self.units if u.state == UnitState.DEAD]
        for dead_unit in dead_units:
            if dead_unit in self.selected_units:
                self.selected_units.remove(dead_unit)
                dead_unit.selected = False
                
        self.units = [u for u in self.units if u.state != UnitState.DEAD]
        
        # 更新AI
        for ai in self.ai_controllers:
            ai.update(self.units, self)
            
        # 更新特效
        self.effects = [e for e in self.effects if e.update(dt)]
        
    def draw(self, screen, camera, sprite_manager):
        """绘制游戏状态"""
        # 绘制星空背景
        for star in self.stars:
            sx, sy = camera.world_to_screen(star['x'], star['y'])
            # 只绘制屏幕可见范围内的星星
            if -50 <= sx <= screen.get_width() + 50 and -50 <= sy <= screen.get_height() + 50:
                size = int(star['size'] * camera.zoom)
                if size > 0:
                    pygame.draw.circle(screen, star['color'], (sx, sy), size)
        
        # 绘制地形
        self.terrain_manager.draw(screen, camera)
        
        # 绘制背景图片（如果有）
        if self.background_image:
            # 计算背景位置（视差效果）
            bg_x = -camera.x * 0.5
            bg_y = -camera.y * 0.5
            # 确保背景图片适配屏幕
            bg_rect = self.background_image.get_rect()
            bg_rect.x = bg_x
            bg_rect.y = bg_y
            screen.blit(self.background_image, bg_rect)
        
        # 按层次绘制单位（先绘制背景单位，再绘制前景单位）
        # 按Y坐标排序，实现简单的深度效果
        sorted_units = sorted(self.units, key=lambda u: u.y)
        
        for unit in sorted_units:
            unit.draw(screen, camera, sprite_manager)
        
        # 绘制投射物（在单位之后，特效之前）
        for projectile in self.projectiles:
            projectile.draw(screen, camera)
                
        # 绘制特效（在单位之上）
        for effect in self.effects:
            effect.draw(screen, camera)
            
        # 绘制选择指示器
        self.draw_selection_indicators(screen, camera)
        
    def draw_selection_indicators(self, screen, camera):
        """绘制选择指示器"""
        for unit in self.units:
            if unit.selected:
                screen_x, screen_y = camera.world_to_screen(unit.x, unit.y)
                radius = int((unit.radius + 8) * camera.zoom)
                
                # 绘制脉动的选择圈
                import time
                pulse = (math.sin(time.time() * 4) + 1) / 2  # 0-1之间的脉动值
                alpha = int(100 + pulse * 155)  # 100-255之间的透明度
                
                # 友方和敌方使用不同颜色
                color = COLOR_WHITE if unit.team == self.player_team else COLOR_YELLOW
                
                # 创建一个临时表面来实现透明度效果
                temp_surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(temp_surface, (*color, alpha), 
                                 (radius + 2, radius + 2), radius, 2)
                screen.blit(temp_surface, (screen_x - radius - 2, screen_y - radius - 2))
                
    def reset(self):
        """重置游戏状态"""
        self.units.clear()
        self.effects.clear()
        self.projectiles.clear()
        self.selected_units.clear()
        self.ai_controllers.clear()
        self.background_image = None
        self.game_paused = False
        self.terrain_manager = TerrainManager()
        self.generate_starfield()

        
    def save_state(self):
        """保存游戏状态（用于暂停/恢复等功能）"""
        # 这里可以实现游戏状态的保存逻辑
        # 返回包含所有必要信息的字典
        state = {
            'units_count': len(self.units),
            'effects_count': len(self.effects),
            'projectiles_count': len(self.projectiles),
            'selected_count': len(self.selected_units),
            'player_team': self.player_team,
            'game_paused': self.game_paused
        }
        return state
        
    def load_state(self, state):
        """加载游戏状态"""
        # 这里可以实现游戏状态的加载逻辑
        # 从保存的状态字典中恢复游戏
        self.player_team = state.get('player_team', 0)
        self.game_paused = state.get('game_paused', False)
        # 其他状态恢复逻辑...
        
    def is_position_valid(self, x, y, unit_radius=0):
        """检查位置是否有效（不被地形阻挡）"""
        return not self.terrain_manager.is_position_blocked(x, y, unit_radius)
        
    def find_clear_position_near(self, target_x, target_y, unit_radius=0, max_attempts=10):
        """在目标位置附近找到一个无阻挡的位置"""
        if self.is_position_valid(target_x, target_y, unit_radius):
            return target_x, target_y
            
        # 尝试在附近找位置
        for attempt in range(max_attempts):
            angle = random.random() * 2 * math.pi
            distance = (attempt + 1) * 30  # 逐渐增大搜索半径
            
            test_x = target_x + math.cos(angle) * distance
            test_y = target_y + math.sin(angle) * distance
            
            if self.is_position_valid(test_x, test_y, unit_radius):
                return test_x, test_y
                
        # 如果找不到合适位置，返回原位置
        return target_x, target_y
        
    def get_units_in_range(self, center_x, center_y, radius, team=None, unit_type=None):
        """获取指定范围内的单位"""
        from units import UnitState
        units_in_range = []
        
        for unit in self.units:
            if unit.state == UnitState.DEAD:
                continue
                
            if team is not None and unit.team != team:
                continue
                
            if unit_type is not None and unit.unit_type != unit_type:
                continue
                
            distance = math.sqrt((unit.x - center_x)**2 + (unit.y - center_y)**2)
            if distance <= radius:
                units_in_range.append(unit)
                
        return units_in_range
        
    def spawn_unit(self, unit_class, x, y, team, unit_data):
        """生成新单位"""
        # 确保位置有效
        valid_x, valid_y = self.find_clear_position_near(x, y, unit_data.get('radius', 20))
        
        # 创建单位
        unit = unit_class(valid_x, valid_y, team, unit_data)
        self.add_unit(unit)
        return unit
        
    def remove_unit(self, unit):
        """移除单位"""
        if unit in self.units:
            self.units.remove(unit)
        if unit in self.selected_units:
            self.selected_units.remove(unit)
            unit.selected = False
            
    def handle_collision(self, unit1, unit2):
        """处理单位碰撞"""
        distance = unit1.distance_to(unit2)
        min_distance = unit1.radius + unit2.radius
        
        if distance < min_distance and distance > 0:
            # 计算推开的方向
            dx = unit2.x - unit1.x
            dy = unit2.y - unit1.y
            
            # 单位化方向向量
            dx /= distance
            dy /= distance
            
            # 推开单位
            overlap = min_distance - distance
            push_distance = overlap / 2
            
            unit1.x -= dx * push_distance
            unit1.y -= dy * push_distance
            unit2.x += dx * push_distance
            unit2.y += dy * push_distance
            
    def update_collisions(self):
        """更新所有单位之间的碰撞"""
        from units import UnitState
        
        for i in range(len(self.units)):
            for j in range(i + 1, len(self.units)):
                unit1 = self.units[i]
                unit2 = self.units[j]
                
                # 跳过死亡单位
                if unit1.state == UnitState.DEAD or unit2.state == UnitState.DEAD:
                    continue
                    
                # 检查并处理碰撞
                self.handle_collision(unit1, unit2)
                
    def get_unit_by_id(self, unit_id):
        """通过ID获取单位"""
        for unit in self.units:
            if hasattr(unit, 'id') and unit.id == unit_id:
                return unit
        return None
        
    def get_units_by_type(self, unit_type):
        """获取指定类型的所有单位"""
        from units import UnitState
        return [u for u in self.units 
                if u.unit_type == unit_type and u.state != UnitState.DEAD]
                
    def count_units(self, team=None, unit_type=None):
        """统计单位数量"""
        from units import UnitState
        count = 0
        
        for unit in self.units:
            if unit.state == UnitState.DEAD:
                continue
                
            if team is not None and unit.team != team:
                continue
                
            if unit_type is not None and unit.unit_type != unit_type:
                continue
                
            count += 1
            
        return count
        
    def get_center_of_units(self, units):
        """获取单位群的中心位置"""
        if not units:
            return 0, 0
            
        total_x = sum(u.x for u in units)
        total_y = sum(u.y for u in units)
        
        return total_x / len(units), total_y / len(units)
        
    def is_game_over(self):
        """检查游戏是否结束"""
        from units import UnitType
        
        # 检查是否有任一方的所有单位都被消灭
        player_alive = self.count_units(team=self.player_team) > 0
        enemy_alive = self.count_units(team=1 - self.player_team) > 0
        
        if not player_alive or not enemy_alive:
            return True
            
        # 检查母舰是否被摧毁
        player_mothership = self.get_mothership(self.player_team)
        enemy_mothership = self.get_mothership(1 - self.player_team)
        
        if (player_mothership and player_mothership.state.value == "dead") or \
           (enemy_mothership and enemy_mothership.state.value == "dead"):
            return True
            
        return False
        
    def get_winner(self):
        """获取胜利方"""
        player_alive = self.count_units(team=self.player_team) > 0
        enemy_alive = self.count_units(team=1 - self.player_team) > 0
        
        if player_alive and not enemy_alive:
            return self.player_team
        elif enemy_alive and not player_alive:
            return 1 - self.player_team
            
        # 检查母舰状态
        player_mothership = self.get_mothership(self.player_team)
        enemy_mothership = self.get_mothership(1 - self.player_team)
        
        if player_mothership and player_mothership.state.value != "dead" and \
           (not enemy_mothership or enemy_mothership.state.value == "dead"):
            return self.player_team
        elif enemy_mothership and enemy_mothership.state.value != "dead" and \
             (not player_mothership or player_mothership.state.value == "dead"):
            return 1 - self.player_team
            
        return None  # 没有胜利方