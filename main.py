import pygame
import sys
import math
from config import *
from camera import Camera
from game_state import GameState
from level_manager import LevelManager
from sprite_manager import SpriteManager
from menu import ContextMenu, MainMenu, GlobalCommandMenu
from command_system import CommandSystem
from ui_panel import UnitPanel
from score_system import ScoreSystem
from units import UnitType, UnitState

class RTSGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("即时策略游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.game_state = GameState()
        self.level_manager = LevelManager()
        self.sprite_manager = SpriteManager()
        self.context_menu = ContextMenu()
        self.global_menu = GlobalCommandMenu()
        self.command_system = CommandSystem()
        self.unit_panel = UnitPanel()
        self.score_system = ScoreSystem()
        self.font = get_font(36)
        self.small_font = get_font(20)
        
        # 选择框
        self.selection_start = None
        self.selection_rect = None
        
    def reset_game_state(self):
        """重置游戏状态"""
        self.game_state.reset()
        self.command_system = CommandSystem()
        self.context_menu.hide()
        self.global_menu.hide()
        self.camera.stop_following()
        self.score_system = ScoreSystem()
        
    def show_score_screen(self, level_name, score, score_breakdown, is_new_record):
        """显示分数画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 30, 0))
        
        # 字体
        title_font = get_font(48)
        score_font = get_font(36)
        detail_font = get_font(20)
        
        # 等待用户输入
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    
            # 继续绘制游戏画面作为背景
            self.screen.fill(COLOR_BLACK)
            self.game_state.draw(self.screen, self.camera, self.sprite_manager)
            
            # 绘制分数覆盖层
            self.screen.blit(overlay, (0, 0))
            
            # 标题
            if is_new_record:
                title_text = title_font.render("新纪录！", True, COLOR_GOLD)
            else:
                title_text = title_font.render("关卡完成", True, COLOR_WHITE)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(title_text, title_rect)
            
            # 总分
            score_text = score_font.render(f"总分: {score}", True, COLOR_YELLOW)
            score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(score_text, score_rect)
            
            # 分数详情
            y_offset = 240
            for category, value in score_breakdown.items():
                detail_text = detail_font.render(f"{category}: {value}", True, COLOR_WHITE)
                detail_rect = detail_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                self.screen.blit(detail_text, detail_rect)
                y_offset += 30
                
            # 最高分
            high_score = self.score_system.get_high_score(level_name)
            high_score_text = detail_font.render(f"最高分: {high_score}", True, COLOR_GOLD)
            high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH // 2, y_offset + 20))
            self.screen.blit(high_score_text, high_score_rect)
            
            # 继续提示
            continue_text = self.small_font.render("按任意键返回主菜单", True, COLOR_LIGHT_GRAY)
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
            self.screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            self.clock.tick(30)
            
        return True

    def show_defeat_screen(self):
        """显示失败画面"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((50, 0, 0))
        
        defeat_font = get_font(72)
        defeat_text = defeat_font.render("失败！", True, COLOR_ENEMY)
        defeat_rect = defeat_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        
        continue_text = self.font.render("按任意键返回主菜单", True, COLOR_WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        
        # 显示失败画面
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
                    
            # 继续绘制游戏画面作为背景
            self.screen.fill(COLOR_BLACK)
            self.game_state.draw(self.screen, self.camera, self.sprite_manager)
            
            # 绘制失败覆盖层
            self.screen.blit(overlay, (0, 0))
            self.screen.blit(defeat_text, defeat_rect)
            self.screen.blit(continue_text, continue_rect)
            
            pygame.display.flip()
            self.clock.tick(30)
            
        return True

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        dt = self.clock.get_time() / 1000.0
        
        # 更新相机
        self.camera.update(keys, mouse_buttons, mouse_pos, dt)
        
        # 更新命令系统光标
        self.command_system.update_cursor(mouse_pos, self.camera, self.game_state)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    # 优先检查右键菜单和全体菜单
                    if self.global_menu.active:
                        option = self.global_menu.get_clicked_option(*mouse_pos)
                        if option:
                            self.execute_global_command(option)
                        self.hide_all_menus()
                    elif self.context_menu.active:
                        option = self.context_menu.get_clicked_option(*mouse_pos)
                        if option:
                            self.execute_menu_option(option[1])
                        else:
                            self.hide_all_menus()
                    elif self.command_system.mode == CommandMode.SELECTING_TARGET:
                        # 左键确认目标选择
                        self.command_system.execute_command_at_position(self.game_state, self.camera)
                        self.game_state.resume_game()
                        self.camera.enable_edge_scroll(False)
                        if self.command_system.valid_target:
                            self.camera.set_follow_target(self.command_system.valid_target)
                    else:
                        # 检查是否点击了单位面板
                        panel_result = self.unit_panel.handle_click(*mouse_pos, self.game_state, button=1)
                        if panel_result:
                            action, unit = panel_result
                            if action == "select":
                                self.game_state.select_unit(unit)
                                self.camera.set_follow_target(unit)
                        else:
                            # 游戏区域点击 - 单击选择单位（包括敌方）
                            self.select_unit_at_position(mouse_pos)
                        
                elif event.button == 3:  # 右键
                    if self.command_system.mode == CommandMode.SELECTING_TARGET:
                        # 取消目标选择
                        self.command_system.cancel_command()
                        self.game_state.resume_game()
                        self.camera.enable_edge_scroll(False)
                    else:
                        # 先检查单位面板右键
                        panel_result = self.unit_panel.handle_click(*mouse_pos, self.game_state, button=3)
                        if panel_result:
                            action, unit = panel_result
                            if action == "select_and_menu":
                                self.game_state.select_unit(unit)
                                self.camera.set_follow_target(unit)
                                self.show_context_menu(mouse_pos)
                        else:
                            # 检查是否右键点击了游戏区域的单位
                            world_x, world_y = self.camera.screen_to_world(*mouse_pos)
                            clicked_unit = self.game_state.get_unit_at_position(world_x, world_y)
                            
                            if clicked_unit:
                                if clicked_unit.team == self.game_state.player_team:
                                    # 右键友方单位：选择并显示菜单
                                    self.game_state.select_unit(clicked_unit)
                                    self.show_context_menu(mouse_pos)
                                else:
                                    # 右键敌方单位：直接攻击
                                    if self.game_state.selected_units:
                                        self.execute_direct_unit_command(clicked_unit)
                            else:
                                # 右键空地：如果有选中单位则显示菜单
                                if self.game_state.selected_units:
                                    self.show_context_menu(mouse_pos)
                        
                elif event.button == 4:  # 滚轮上
                    # 优先处理面板滚动
                    if (self.unit_panel.visible and 
                        self.unit_panel.x <= mouse_pos[0] <= self.unit_panel.x + self.unit_panel.width and
                        self.unit_panel.y <= mouse_pos[1] <= self.unit_panel.y + self.unit_panel.height):
                        self.unit_panel.handle_scroll(1)
                    else:
                        self.camera.zoom_in()
                elif event.button == 5:  # 滚轮下
                    # 优先处理面板滚动
                    if (self.unit_panel.visible and 
                        self.unit_panel.x <= mouse_pos[0] <= self.unit_panel.x + self.unit_panel.width and
                        self.unit_panel.y <= mouse_pos[1] <= self.unit_panel.y + self.unit_panel.height):
                        self.unit_panel.handle_scroll(-1)
                    else:
                        self.camera.zoom_out()
                    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.command_system.mode == CommandMode.SELECTING_TARGET:
                        self.command_system.cancel_command()
                        self.game_state.resume_game()
                        self.camera.enable_edge_scroll(False)
                    elif self.context_menu.active or self.global_menu.active:
                        self.hide_all_menus()
                    else:
                        # ESC键返回主菜单
                        return "main_menu"
                elif event.key == pygame.K_TAB:
                    # Tab键切换面板显示
                    self.unit_panel.toggle_visibility()
                    
        return "continue"
        
    def select_unit_at_position(self, mouse_pos):
        """在指定位置选择单位"""
        world_x, world_y = self.camera.screen_to_world(*mouse_pos)
        clicked_unit = self.game_state.get_unit_at_position(world_x, world_y)
        
        if clicked_unit:
            # 选择单位（友方或敌方）
            self.game_state.select_unit(clicked_unit)
            self.camera.set_follow_target(clicked_unit)
        else:
            # 点击空地，解除视角跟踪
            self.camera.stop_following()
            self.game_state.clear_selection()
                    
    def show_context_menu(self, mouse_pos):
        """显示右键菜单"""
        if not self.game_state.selected_units:
            return
            
        # 暂停游戏
        self.game_state.pause_game()
        
        # 隐藏其他菜单
        self.context_menu.hide()
        self.global_menu.hide()
            
        unit = self.game_state.selected_units[0]
        options = []
        
        # 根据单位类型生成菜单
        if unit.unit_type == UnitType.MOTHERSHIP:
            options.append(("全体命令", "global"))
            options.append(("移动", "move"))
            options.append(("攻击", "attack"))
            options.append(("修理", "repair"))
        elif unit.unit_type == UnitType.REPAIR:
            options.append(("全体命令", "global"))##
            options.append(("移动", "move"))
            options.append(("跟随", "follow"))
            options.append(("修理", "repair"))
            options.append(("补给", "supply"))
            if unit.sp >= unit.max_sp:
                options.append(("必杀技", "skill"))
        else:  # 其他战斗单位
            options.append(("全体命令", "global"))##
            options.append(("移动", "move"))
            options.append(("攻击", "attack"))
            options.append(("跟随", "follow"))
            options.append(("补给", "supply"))
            if unit.sp >= unit.max_sp:
                options.append(("必杀技", "skill"))
        
        self.context_menu.show(*mouse_pos, options)
        
    def hide_all_menus(self):
        """隐藏所有菜单"""
        self.context_menu.hide()
        self.global_menu.hide()
        # 只有在不是选择目标模式时才恢复游戏
        if self.command_system.mode != CommandMode.SELECTING_TARGET:
            self.game_state.resume_game()
        
    def execute_menu_option(self, action):
        """执行菜单选项"""
        if action == "global":
            # 显示全体命令菜单（在原菜单右侧）
            self.global_menu.show_beside(self.context_menu)
            # 保持暂停状态，不隐藏原菜单
        elif action in ["move", "attack", "follow", "repair"]:
            # 需要选择目标的命令
            self.command_system.start_target_selection(action, self.game_state.selected_units)
            self.hide_all_menus()
            # 进入选择目标模式，保持暂停
            self.camera.enable_edge_scroll(True)
        elif action in ["supply", "skill"]:
            # 直接执行的命令
            self.command_system.execute_direct_command(action, self.game_state.selected_units, self.game_state)
            self.hide_all_menus()
            
    def execute_global_command(self, action):
        """执行全体命令"""
        # 获取所有友方非母舰单位（包括修理机）
        all_units = self.game_state.get_all_friendly_units(self.game_state.player_team)
        
        if action in ["移动", "攻击", "跟随"]:
            # 转换命令名称
            command_map = {"移动": "move", "攻击": "attack", "跟随": "follow"}
            self.command_system.start_target_selection(command_map[action], all_units)
            self.hide_all_menus()
            self.camera.enable_edge_scroll(True)
        elif action == "补给":
            self.command_system.execute_direct_command("supply", all_units, self.game_state)
            self.hide_all_menus()
            
    def execute_direct_unit_command(self, clicked_unit):
        """直接对点击的单位执行命令"""
        if not self.game_state.selected_units:
            return
            
        for selected_unit in self.game_state.selected_units:
            if clicked_unit.team != self.game_state.player_team:
                # 点击敌方单位 - 执行攻击
                if selected_unit.attack_damage > 0 and selected_unit.unit_type != UnitType.REPAIR:
                    selected_unit.attack_target = clicked_unit
                    selected_unit.target = clicked_unit
                    selected_unit.state = UnitState.ATTACKING
            else:
                # 点击友方单位
                if selected_unit.unit_type == UnitType.REPAIR or selected_unit.unit_type == UnitType.MOTHERSHIP:
                    # 修理机或母舰对受损友军进行修理
                    if clicked_unit.hp < clicked_unit.max_hp:
                        selected_unit.repair_target = clicked_unit
                        selected_unit.target = clicked_unit
                        selected_unit.state = UnitState.REPAIRING
                else:
                    # 其他单位执行跟随
                    selected_unit.follow_target = clicked_unit
                    selected_unit.state = UnitState.FOLLOWING
                    selected_unit.attack_target = None
                    selected_unit.repair_target = None
    
    def play_level(self, level_index):
        """游玩指定关卡"""
        # 重置游戏状态
        self.reset_game_state()
        
        # 加载关卡
        if not self.level_manager.load_level(level_index, self.game_state, self.sprite_manager):
            print("加载关卡失败")
            return "main_menu"
            
        # 获取关卡信息
        level_data = self.level_manager.current_level_data
        level_name = level_data.get('name', '未知关卡')
        
        # 统计初始单位数量
        player_units_count = len([u for u in self.game_state.units if u.team == self.game_state.player_team])
        enemy_units_count = len([u for u in self.game_state.units if u.team != self.game_state.player_team])
        
        # 开始计分
        self.score_system.start_level(player_units_count, enemy_units_count)
            
        # 自动将视角居中到地图中心
        center_x, center_y = self.level_manager.get_map_center(self.game_state)
        self.camera.focus_on(center_x, center_y)
        
        # 游戏主循环
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 处理输入
            input_result = self.handle_input()
            if input_result == "main_menu":
                return "main_menu"
            
            # 更新左侧面板
            self.unit_panel.update(self.game_state)
            
            # 更新游戏状态
            self.game_state.update(dt)
            
            # 检查胜利/失败条件
            if not self.game_state.is_paused():
                if self.level_manager.check_victory(self.game_state):
                    # 计算分数
                    score, score_breakdown = self.score_system.end_level(self.game_state)
                    is_new_record = self.score_system.save_high_score(level_name, score)
                    
                    if self.show_score_screen(level_name, score, score_breakdown, is_new_record):
                        return "main_menu"
                    else:
                        self.running = False
                        return "quit"
                    
                elif self.level_manager.check_defeat(self.game_state):
                    if self.show_defeat_screen():
                        return "main_menu"
                    else:
                        self.running = False
                        return "quit"
                
            # 绘制游戏
            self.screen.fill(COLOR_BLACK)
            self.game_state.draw(self.screen, self.camera, self.sprite_manager)
            
            # 绘制命令光标
            self.command_system.draw_cursor(self.screen, self.camera)
            
            # 绘制UI信息
            if self.game_state.selected_units:
                level_text = self.small_font.render(f"关卡: {level_name}", True, COLOR_WHITE)
                self.screen.blit(level_text, (10, 10))
                
                # 显示选中单位的详细信息
                if len(self.game_state.selected_units) == 1:
                    unit = self.game_state.selected_units[0]
                    info_lines = [
                        f"单位: {unit.name}",
                        f"描述: {unit.description}",
                        f"血量: {int(unit.hp)}/{unit.max_hp}",
                    ]
                    
                    if unit.max_energy > 0:
                        info_lines.append(f"能量: {int(unit.energy)}/{unit.max_energy}")
                    if unit.max_sp > 0:
                        info_lines.append(f"SP: {int(unit.sp)}/{unit.max_sp}")
                    if unit.shield > 0:
                        info_lines.append(f"护盾: {int(unit.shield)}")
                        
                    for i, line in enumerate(info_lines):
                        text = self.small_font.render(line, True, COLOR_WHITE)
                        self.screen.blit(text, (10, 30 + i * 18))
            
            # 绘制单位面板（覆盖在游戏画面上）
            self.unit_panel.draw(self.screen, self.game_state)
            
            # 绘制右键菜单（最高优先级）
            self.context_menu.draw(self.screen)
            self.global_menu.draw(self.screen)
            
            # 绘制游戏状态提示
            if self.command_system.mode == CommandMode.SELECTING_TARGET:
                pause_text = self.font.render("选择目标中... (左键确认, 右键取消)", True, COLOR_YELLOW)
                text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                self.screen.blit(pause_text, text_rect)
            elif self.game_state.is_paused():
                pause_text = self.font.render("游戏已暂停", True, COLOR_YELLOW)
                text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                self.screen.blit(pause_text, text_rect)
            
            # 绘制控制提示
            hints = [
                "TAB:显示/隐藏单位面板 | 中键:拖动视角 | ESC:返回主菜单",
                "左键:选择 | 右键:菜单/命令 | 滚轮:缩放/面板滚动"
            ]
            for i, hint in enumerate(hints):
                hint_text = self.small_font.render(hint, True, (200, 200, 200))
                hint_rect = hint_text.get_rect()
                hint_rect.right = SCREEN_WIDTH - 10
                hint_rect.bottom = SCREEN_HEIGHT - 10 - i * 25
                self.screen.blit(hint_text, hint_rect)
            
            pygame.display.flip()
            
        return "quit"
                
    def run(self):
        """主运行循环"""
        while self.running:
            # 显示主菜单
            menu = MainMenu(self.screen, self.level_manager)
            selected_level = menu.run()
            
            if selected_level is None:
                break
                
            # 游玩选中的关卡
            result = self.play_level(selected_level)
            if result == "quit":
                break
            # 如果result == "main_menu"，则继续循环回到主菜单
            
        pygame.quit()

if __name__ == "__main__":
    game = RTSGame()
    game.run()