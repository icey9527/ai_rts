import pygame
import math
from config import *
from units import UnitType

class CommandSystem:
    def __init__(self):
        self.mode = CommandMode.NORMAL
        self.pending_command = None
        self.pending_units = []
        self.cursor_pos = (0, 0)
        self.valid_target = None
        
    def start_target_selection(self, command_type, units):
        """开始目标选择模式"""
        self.mode = CommandMode.SELECTING_TARGET
        self.pending_command = command_type
        self.pending_units = units.copy()
        
    def update_cursor(self, mouse_pos, camera, game_state):
        """更新光标位置和有效目标"""
        if self.mode == CommandMode.SELECTING_TARGET:
            self.cursor_pos = camera.screen_to_world(*mouse_pos)
            self.valid_target = self.find_valid_target(game_state)
            
    def find_valid_target(self, game_state):
        """查找有效目标"""
        cursor_x, cursor_y = self.cursor_pos
        
        for unit in game_state.units:
            distance = math.sqrt((unit.x - cursor_x)**2 + (unit.y - cursor_y)**2)
            if distance < unit.radius:
                if self.pending_command == "attack" and unit.team != 0:
                    return unit
                elif self.pending_command == "follow" and unit.team == 0:
                    return unit
                elif self.pending_command == "repair" and unit.team == 0 and unit.hp < unit.max_hp:
                    return unit
        return None
        
    def execute_command_at_position(self, game_state, camera):
        """在当前光标位置执行命令"""
        if self.mode == CommandMode.SELECTING_TARGET and self.pending_command:
            if self.pending_command == "move":
                self.execute_move_command()
            elif self.valid_target:
                if self.pending_command == "attack":
                    self.execute_attack_command()
                elif self.pending_command == "follow":
                    self.execute_follow_command()
                elif self.pending_command == "repair":
                    self.execute_repair_command()
                    
        self.cancel_command()
        
    def execute_move_command(self):
        """执行移动命令"""
        from units import UnitState
        for unit in self.pending_units:
            unit.target_pos = self.cursor_pos
            unit.state = UnitState.MOVING
            unit.target = None
            unit.attack_target = None
            unit.repair_target = None
            
    def execute_attack_command(self):
        """执行攻击(追击)命令"""
        from units import UnitState
        for unit in self.pending_units:
            if unit.attack_damage > 0 and unit.unit_type != UnitType.REPAIR:
                unit.attack_target = self.valid_target
                unit.target = self.valid_target
                unit.state = UnitState.ATTACKING
                
    def execute_follow_command(self):
        """执行跟随命令"""
        from units import UnitState
        for unit in self.pending_units:
            unit.follow_target = self.valid_target
            unit.state = UnitState.FOLLOWING
            unit.attack_target = None
            unit.repair_target = None
            
    def execute_repair_command(self):
        """执行修理命令"""
        from units import UnitState
        for unit in self.pending_units:
            if unit.unit_type == UnitType.REPAIR or unit.unit_type == UnitType.MOTHERSHIP:
                unit.repair_target = self.valid_target
                unit.target = self.valid_target
                unit.state = UnitState.REPAIRING
                
    def execute_direct_command(self, command_type, units, game_state):
        """执行直接命令（不需要选择目标）"""
        from units import UnitState
        
        if command_type == "supply":
            for unit in units:
                if unit.unit_type != UnitType.MOTHERSHIP:
                    unit.state = UnitState.RETURNING
                    unit.attack_target = None
                    unit.repair_target = None
                    
        elif command_type == "skill":
            for unit in units:
                if unit.unit_type != UnitType.MOTHERSHIP and unit.sp >= unit.max_sp:
                    unit.use_skill(game_state.units, game_state)
                    
    def cancel_command(self):
        """取消命令"""
        self.mode = CommandMode.NORMAL
        self.pending_command = None
        self.pending_units = []
        self.valid_target = None
        
    def draw_cursor(self, screen, camera):
        """绘制命令光标"""
        if self.mode == CommandMode.SELECTING_TARGET and self.pending_units:
            # 为每个单位绘制箭头
            for unit in self.pending_units:
                start_x, start_y = camera.world_to_screen(unit.x, unit.y)
                end_x, end_y = camera.world_to_screen(*self.cursor_pos)
                
                # 根据命令类型选择颜色
                if self.pending_command == "attack":
                    color = COLOR_ENEMY if self.valid_target else COLOR_GRAY
                elif self.pending_command == "follow":
                    color = COLOR_YELLOW if self.valid_target else COLOR_GRAY
                elif self.pending_command == "repair":
                    color = (0, 255, 0) if self.valid_target else COLOR_GRAY  # 绿色
                elif self.pending_command == "move":
                    color = COLOR_WHITE
                else:
                    color = COLOR_WHITE
                    
                # 绘制长箭头
                self.draw_long_arrow(screen, start_x, start_y, end_x, end_y, color)
            
            # 在目标位置绘制额外指示器
            end_x, end_y = camera.world_to_screen(*self.cursor_pos)
            if self.valid_target:
                self.draw_target_indicator(screen, end_x, end_y, color)
            else:
                self.draw_position_indicator(screen, end_x, end_y, color)
                
    def draw_long_arrow(self, screen, start_x, start_y, end_x, end_y, color):
        """绘制长箭头"""
        # 计算箭头方向
        dx = end_x - start_x
        dy = end_y - start_y
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 10:  # 太短就不画
            return
            
        # 单位化方向向量
        dx /= length
        dy /= length
        
        # 绘制箭头主线
        pygame.draw.line(screen, color, (start_x, start_y), (end_x, end_y), 3)
        
        # 绘制箭头头部
        arrow_length = min(20, length * 0.2)  # 箭头头部长度
        arrow_angle = 0.5  # 箭头角度
        
        # 计算箭头两个分支的端点
        left_x = end_x - arrow_length * (dx * math.cos(arrow_angle) - dy * math.sin(arrow_angle))
        left_y = end_y - arrow_length * (dy * math.cos(arrow_angle) + dx * math.sin(arrow_angle))
        
        right_x = end_x - arrow_length * (dx * math.cos(-arrow_angle) - dy * math.sin(-arrow_angle))
        right_y = end_y - arrow_length * (dy * math.cos(-arrow_angle) + dx * math.sin(-arrow_angle))
        
        # 绘制箭头头部
        pygame.draw.line(screen, color, (end_x, end_y), (left_x, left_y), 3)
        pygame.draw.line(screen, color, (end_x, end_y), (right_x, right_y), 3)
        
    def draw_target_indicator(self, screen, x, y, color):
        """绘制目标指示器"""
        # 绘制目标圈
        pygame.draw.circle(screen, color, (int(x), int(y)), 15, 2)
        pygame.draw.circle(screen, color, (int(x), int(y)), 8, 2)
        
    def draw_position_indicator(self, screen, x, y, color):
        """绘制位置指示器"""
        # 绘制位置标记
        pygame.draw.circle(screen, color, (int(x), int(y)), 8, 2)
        # 绘制十字
        pygame.draw.line(screen, color, (x-6, y), (x+6, y), 2)
        pygame.draw.line(screen, color, (x, y-6), (x, y+6), 2)