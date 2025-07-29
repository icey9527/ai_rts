import pygame
from config import *

class ContextMenu:
    def __init__(self):
        self.active = False
        self.x = 0
        self.y = 0
        self.options = []
        self.font = get_font(20)
        self.padding = 5
        self.item_height = 25
        self.width = 150
        
    def show(self, x, y, options):
        self.active = True
        self.x = x
        self.y = y
        self.options = options
        
    def hide(self):
        self.active = False
        
    def get_clicked_option(self, mouse_x, mouse_y):
        if not self.active:
            return None
            
        if (self.x <= mouse_x <= self.x + self.width and
            self.y <= mouse_y <= self.y + len(self.options) * self.item_height):
            index = (mouse_y - self.y) // self.item_height
            if 0 <= index < len(self.options):
                return self.options[index]
        return None
        
    def draw(self, screen):
        if not self.active:
            return
            
        height = len(self.options) * self.item_height
        pygame.draw.rect(screen, (50, 50, 50), 
                        (self.x, self.y, self.width, height))
        pygame.draw.rect(screen, COLOR_GRAY, 
                        (self.x, self.y, self.width, height), 1)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, option in enumerate(self.options):
            y = self.y + i * self.item_height
            
            if (self.x <= mouse_x <= self.x + self.width and
                y <= mouse_y <= y + self.item_height):
                pygame.draw.rect(screen, (70, 70, 70), 
                               (self.x, y, self.width, self.item_height))
                
            text = self.font.render(option[0], True, COLOR_WHITE)
            screen.blit(text, (self.x + self.padding, y + self.padding))

class MainMenu:
    def __init__(self, screen, level_manager):
        self.screen = screen
        self.level_manager = level_manager
        self.font_title = get_font(48)
        self.font_option = get_font(32)
        self.font_desc = get_font(24)
        self.font_small = get_font(20)
        self.selected_level = 0
        self.scroll_offset = 0
        self.item_height = 80  # 每个关卡项的高度
        self.visible_items = 6  # 可见的关卡数量
        self.list_y_start = 200  # 关卡列表开始的Y坐标
        self.list_height = self.item_height * self.visible_items
        
    def update_scroll(self):
        """更新滚动偏移，确保选中项可见"""
        # 计算选中项的位置
        selected_position = self.selected_level * self.item_height - self.scroll_offset
        
        # 如果选中项在可见区域上方
        if selected_position < 0:
            self.scroll_offset = self.selected_level * self.item_height
            
        # 如果选中项在可见区域下方
        elif selected_position >= self.list_height - self.item_height:
            self.scroll_offset = (self.selected_level - self.visible_items + 1) * self.item_height
            
        # 限制滚动范围
        max_scroll = max(0, (len(self.level_manager.available_levels) - self.visible_items) * self.item_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
    def handle_scroll_wheel(self, direction):
        """处理鼠标滚轮"""
        scroll_speed = self.item_height
        if direction > 0:  # 向上滚动
            self.scroll_offset = max(0, self.scroll_offset - scroll_speed)
        else:  # 向下滚动
            max_scroll = max(0, (len(self.level_manager.available_levels) - self.visible_items) * self.item_height)
            self.scroll_offset = min(max_scroll, self.scroll_offset + scroll_speed)
            
    def get_level_at_position(self, mouse_y):
        """根据鼠标Y坐标获取关卡索引"""
        if mouse_y < self.list_y_start or mouse_y > self.list_y_start + self.list_height:
            return -1
            
        relative_y = mouse_y - self.list_y_start + self.scroll_offset
        index = relative_y // self.item_height
        
        if 0 <= index < len(self.level_manager.available_levels):
            return index
        return -1
        
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        # 创建关卡列表的裁剪区域
        list_rect = pygame.Rect(80, self.list_y_start, SCREEN_WIDTH - 160, self.list_height)
        
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_level = max(0, self.selected_level - 1)
                        self.update_scroll()
                    elif event.key == pygame.K_DOWN:
                        self.selected_level = min(len(self.level_manager.available_levels) - 1, 
                                                self.selected_level + 1)
                        self.update_scroll()
                    elif event.key == pygame.K_RETURN:
                        return self.selected_level
                    elif event.key == pygame.K_ESCAPE:
                        return None
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        # 检查点击了哪个关卡
                        clicked_level = self.get_level_at_position(mouse_pos[1])
                        if clicked_level >= 0:
                            return clicked_level
                    elif event.button == 4:  # 滚轮向上
                        self.handle_scroll_wheel(1)
                    elif event.button == 5:  # 滚轮向下
                        self.handle_scroll_wheel(-1)
                        
                elif event.type == pygame.MOUSEMOTION:
                    # 鼠标悬停选择
                    hovered_level = self.get_level_at_position(mouse_pos[1])
                    if hovered_level >= 0:
                        self.selected_level = hovered_level
                        
            self.screen.fill((20, 20, 40))
            
            # 标题
            title = self.font_title.render("选择关卡", True, COLOR_WHITE)
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(title, title_rect)
            
            # 设置裁剪区域
            self.screen.set_clip(list_rect)
            
            # 绘制关卡列表背景
            pygame.draw.rect(self.screen, (30, 30, 50), list_rect)
            
            # 计算可见的关卡范围
            start_index = max(0, self.scroll_offset // self.item_height)
            end_index = min(len(self.level_manager.available_levels), 
                          start_index + self.visible_items + 1)
            
            # 关卡列表
            for i in range(start_index, end_index):
                level = self.level_manager.available_levels[i]
                y = self.list_y_start + (i * self.item_height) - self.scroll_offset
                
                # 只绘制在可见区域内的关卡
                if y + self.item_height >= self.list_y_start and y < self.list_y_start + self.list_height:
                    color = COLOR_YELLOW if i == self.selected_level else (200, 200, 200)
                    
                    # 绘制选中背景
                    if i == self.selected_level:
                        pygame.draw.rect(self.screen, (40, 40, 60), 
                                       (80, y - 5, SCREEN_WIDTH - 160, self.item_height))
                    
                    # 关卡名称
                    text = self.font_option.render(level['name'], True, color)
                    self.screen.blit(text, (100, y))
                    
                    # 关卡描述
                    if level['description']:
                        desc = self.font_desc.render(level['description'], True, (150, 150, 150))
                        self.screen.blit(desc, (120, y + 35))
                    
                    # 显示最高分（如果有）
                    from score_system import ScoreSystem
                    score_system = ScoreSystem()
                    high_score = score_system.get_high_score(level['name'])
                    if high_score > 0:
                        score_text = self.font_small.render(f"最高分: {high_score}", True, COLOR_GOLD)
                        score_rect = score_text.get_rect()
                        score_rect.right = SCREEN_WIDTH - 100
                        score_rect.centery = y + self.item_height // 2
                        self.screen.blit(score_text, score_rect)
            
            # 取消裁剪
            self.screen.set_clip(None)
            
            # 绘制列表边框
            pygame.draw.rect(self.screen, COLOR_GRAY, list_rect, 2)
            
            # 绘制滚动条（如果需要）
            total_height = len(self.level_manager.available_levels) * self.item_height
            if total_height > self.list_height:
                # 滚动条背景
                scrollbar_x = SCREEN_WIDTH - 70
                scrollbar_y = self.list_y_start
                scrollbar_width = 10
                scrollbar_height = self.list_height
                
                pygame.draw.rect(self.screen, (50, 50, 50), 
                               (scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height))
                
                # 滚动条滑块
                thumb_height = max(20, int(self.list_height * self.list_height / total_height))
                thumb_y = scrollbar_y + int(self.scroll_offset * (self.list_height - thumb_height) / (total_height - self.list_height))
                
                pygame.draw.rect(self.screen, COLOR_LIGHT_GRAY, 
                               (scrollbar_x, thumb_y, scrollbar_width, thumb_height))
                
            # 显示关卡数量信息
            info_text = self.font_small.render(f"共 {len(self.level_manager.available_levels)} 关", 
                                             True, (150, 150, 150))
            info_rect = info_text.get_rect()
            info_rect.centerx = SCREEN_WIDTH // 2
            info_rect.y = self.list_y_start + self.list_height + 20
            self.screen.blit(info_text, info_rect)
            
            # 操作提示
            hint = self.font_desc.render("↑↓选择 | 回车确认 | 鼠标点击/滚轮 | ESC退出", 
                                       True, (150, 150, 150))
            hint_rect = hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(hint, hint_rect)
            
            pygame.display.flip()
            clock.tick(30)
            
        return None

class GlobalCommandMenu:
    """全体命令菜单"""
    def __init__(self):
        self.active = False
        self.x = 0
        self.y = 0
        self.font = get_font(20)
        self.options = ["移动", "攻击", "跟随", "补给"]
        self.width = 120
        self.item_height = 25
        
    def show_beside(self, context_menu):
        """在右键菜单旁边显示"""
        if context_menu.active:
            self.active = True
            self.x = context_menu.x + context_menu.width + 5  # 在右侧显示
            self.y = context_menu.y
        
    def show(self, x, y):
        self.active = True
        self.x = x
        self.y = y
        
    def hide(self):
        self.active = False
        
    def get_clicked_option(self, mouse_x, mouse_y):
        if not self.active:
            return None
            
        if (self.x <= mouse_x <= self.x + self.width and
            self.y <= mouse_y <= self.y + len(self.options) * self.item_height):
            index = (mouse_y - self.y) // self.item_height
            if 0 <= index < len(self.options):
                return self.options[index]
        return None
        
    def draw(self, screen):
        if not self.active:
            return
            
        height = len(self.options) * self.item_height
        pygame.draw.rect(screen, (50, 50, 50), 
                        (self.x, self.y, self.width, height))
        pygame.draw.rect(screen, COLOR_GRAY, 
                        (self.x, self.y, self.width, height), 1)
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        for i, option in enumerate(self.options):
            y = self.y + i * self.item_height
            
            if (self.x <= mouse_x <= self.x + self.width and
                y <= mouse_y <= y + self.item_height):
                pygame.draw.rect(screen, (70, 70, 70), 
                               (self.x, y, self.width, self.item_height))
                
            text = self.font.render(option, True, COLOR_WHITE)
            screen.blit(text, (self.x + 5, y + 5))