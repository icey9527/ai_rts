import pygame
from config import *
from units import UnitState

class UnitPanel:
    def __init__(self):
        self.x = 10  # 固定在左下角
        self.y = SCREEN_HEIGHT - 350
        self.width = 280
        self.height = 340
        self.font = get_font(16)
        self.small_font = get_font(14)
        self.scroll_offset = 0
        self.max_scroll = 0
        self.selected_unit_index = -1
        self.visible = True
        self.unit_height = 50
        
    def update(self, game_state):
        # 获取友方单位列表
        self.friendly_units = [u for u in game_state.units 
                              if u.team == game_state.player_team and u.state.value != "dead"]
        
        # 计算最大滚动距离
        content_height = self.height - 40  # 减去标题和边距
        max_visible = content_height // self.unit_height
        total_units = len(self.friendly_units)
        
        if total_units > max_visible:
            self.max_scroll = (total_units - max_visible) * self.unit_height
        else:
            self.max_scroll = 0
            
        # 限制滚动范围
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        
    def handle_click(self, mouse_x, mouse_y, game_state, button=1):
        """处理面板点击，button=1左键，button=3右键"""
        if not self.visible:
            return None
            
        if not (self.x <= mouse_x <= self.x + self.width and 
                self.y <= mouse_y <= self.y + self.height):
            return None
            
        # 计算点击的单位索引
        relative_y = mouse_y - self.y - 30  # 减去标题高度
        unit_index = int((relative_y + self.scroll_offset) // self.unit_height)
        
        if 0 <= unit_index < len(self.friendly_units):
            unit = self.friendly_units[unit_index]
            if button == 1:  # 左键选择
                return ("select", unit)
            elif button == 3:  # 右键选择并显示菜单
                return ("select_and_menu", unit)
                
        return None
        
    def handle_scroll(self, scroll_direction):
        """处理滚动事件"""
        if not self.visible or self.max_scroll == 0:
            return
            
        scroll_speed = self.unit_height
        if scroll_direction > 0:  # 向上滚动
            self.scroll_offset = max(0, self.scroll_offset - scroll_speed)
        else:  # 向下滚动
            self.scroll_offset = min(self.max_scroll, self.scroll_offset + scroll_speed)
        
    def draw(self, screen, game_state):
        if not self.visible:
            return
            
        # 绘制半透明背景
        panel_surface = pygame.Surface((self.width, self.height))
        panel_surface.set_alpha(220)  # 半透明
        panel_surface.fill(COLOR_DARK_GRAY)
        screen.blit(panel_surface, (self.x, self.y))
        
        # 绘制边框
        pygame.draw.rect(screen, COLOR_GRAY, 
                        (self.x, self.y, self.width, self.height), 2)
        
        # 绘制标题
        title = self.font.render("友方单位", True, COLOR_WHITE)
        screen.blit(title, (self.x + 10, self.y + 5))
        
        # 绘制滚动条（如果需要）
        if self.max_scroll > 0:
            scrollbar_height = max(20, int((self.height - 40) * (self.height - 40) / (len(self.friendly_units) * self.unit_height)))
            scrollbar_y = self.y + 30 + int((self.scroll_offset / self.max_scroll) * (self.height - 40 - scrollbar_height))
            pygame.draw.rect(screen, COLOR_LIGHT_GRAY, 
                           (self.x + self.width - 10, scrollbar_y, 8, scrollbar_height))
        
        # 绘制单位列表
        if hasattr(self, 'friendly_units'):
            y_offset = self.y + 30
            content_height = self.height - 40
            
            # 创建裁剪区域，防止绘制超出面板
            clip_rect = pygame.Rect(self.x, y_offset, self.width - 12, content_height)
            screen.set_clip(clip_rect)
            
            # 计算可见单位范围
            start_index = max(0, self.scroll_offset // self.unit_height)
            end_index = min(len(self.friendly_units), 
                          start_index + (content_height // self.unit_height) + 2)
            
            for i in range(start_index, end_index):
                unit = self.friendly_units[i]
                unit_y = y_offset + (i * self.unit_height) - self.scroll_offset
                
                # 只绘制在可见区域内的单位
                if unit_y + self.unit_height >= y_offset and unit_y <= y_offset + content_height:
                    # 绘制单位背景
                    if unit.selected:
                        back_surface = pygame.Surface((self.width - 16, self.unit_height - 2))
                        back_surface.set_alpha(120)
                        back_surface.fill(COLOR_BLUE)
                        screen.blit(back_surface, (self.x + 2, unit_y))
                    
                    # 绘制单位名称
                    name_text = self.small_font.render(unit.name, True, COLOR_WHITE)
                    screen.blit(name_text, (self.x + 5, unit_y + 2))
                    
                    # 绘制状态文字
                    status_text = self.get_unit_status_text(unit)
                    status_color = self.get_status_color(unit.state)
                    status_surface = self.small_font.render(status_text, True, status_color)
                    status_x = self.x + self.width - status_surface.get_width() - 15
                    screen.blit(status_surface, (status_x, unit_y + 2))
                    
                    # 绘制三个属性条
                    bar_width = self.width - 25
                    bar_height = 6
                    bar_spacing = 2
                    
                    # HP条 (绿色)
                    hp_y = unit_y + 20
                    hp_ratio = unit.hp / unit.max_hp
                    self.draw_bar(screen, self.x + 10, hp_y, bar_width, bar_height, 
                                 hp_ratio, (40, 40, 40), (0, 200, 0))
                    
                    # 能量条 (蓝色) - 只有当max_energy > 0时才显示
                    if unit.max_energy > 0:
                        en_y = hp_y + bar_height + bar_spacing
                        en_ratio = unit.energy / unit.max_energy
                        self.draw_bar(screen, self.x + 10, en_y, bar_width, bar_height, 
                                     en_ratio, (40, 40, 40), (0, 100, 255))
                    else:
                        en_y = hp_y  # 没有能量条时，SP条位置上移
                    
                    # SP条 (黄色) - 只有当max_sp > 0时才显示
                    if unit.max_sp > 0:
                        sp_y = en_y + bar_height + bar_spacing
                        sp_ratio = unit.sp / unit.max_sp
                        self.draw_bar(screen, self.x + 10, sp_y, bar_width, bar_height, 
                                     sp_ratio, (40, 40, 40), (255, 200, 0))
            
            # 取消裁剪
            screen.set_clip(None)
            
    def draw_bar(self, screen, x, y, width, height, ratio, bg_color, fill_color):
        """绘制属性条"""
        # 背景
        pygame.draw.rect(screen, bg_color, (x, y, width, height))
        # 填充
        fill_width = int(width * ratio)
        if fill_width > 0:
            pygame.draw.rect(screen, fill_color, (x, y, fill_width, height))
        # 边框
        pygame.draw.rect(screen, COLOR_GRAY, (x, y, width, height), 1)
                
    def get_unit_status_text(self, unit):
        """获取单位状态文字"""
        state_text = {
            UnitState.IDLE: "待机",
            UnitState.MOVING: "移动",
            UnitState.ATTACKING: "攻击",
            UnitState.REPAIRING: "修理",
            UnitState.RETURNING: "返回",
            UnitState.SUPPLYING: "补给",
            UnitState.FOLLOWING: "跟随",
            UnitState.DISABLED: "禁用",
            UnitState.CIRCLE_STRAFING: "围攻",
            UnitState.DEAD: "阵亡"
        }
        return state_text.get(unit.state, "未知")
        
    def get_status_color(self, state):
        """获取状态颜色"""
        if state == UnitState.IDLE:
            return COLOR_WHITE
        elif state in [UnitState.ATTACKING, UnitState.CIRCLE_STRAFING]:
            return COLOR_ENEMY
        elif state == UnitState.REPAIRING:
            return (0, 255, 0)
        elif state in [UnitState.RETURNING, UnitState.SUPPLYING]:
            return COLOR_BLUE
        elif state == UnitState.FOLLOWING:
            return COLOR_YELLOW
        elif state == UnitState.DISABLED:
            return COLOR_PURPLE
        else:
            return COLOR_GRAY
            
    def toggle_visibility(self):
        """切换面板显示/隐藏"""
        self.visible = not self.visible