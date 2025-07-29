import os
import json
import pygame
from units import Unit, RepairUnit, UnitType, UnitState
from ai import SimpleAI
from improved_ai import AdvancedAI, HyperAggressiveAI, TurtleAI

class LevelManager:
    def __init__(self, levels_folder="levels"):
        self.levels_folder = levels_folder
        self.available_levels = []
        self.current_level_data = None
        self.scan_levels()
        
    def scan_levels(self):
        """扫描关卡文件夹"""
        self.available_levels = []
        if os.path.exists(self.levels_folder):
            for filename in os.listdir(self.levels_folder):
                if filename.endswith('.json'):
                    level_path = os.path.join(self.levels_folder, filename)
                    try:
                        with open(level_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.available_levels.append({
                                'file': filename,
                                'path': level_path,
                                'name': data.get('name', filename),
                                'description': data.get('description', ''),
                                'difficulty': data.get('difficulty', 'normal'),
                                'ai_type': data.get('ai_type', 'advanced')
                            })
                            print(f"Found level: {data.get('name', filename)} (AI: {data.get('ai_type', 'advanced')})")
                    except Exception as e:
                        print(f"Failed to load level {filename}: {e}")
                        
        self.available_levels.sort(key=lambda x: x['file'])
        print(f"Total levels found: {len(self.available_levels)}")
        
    def get_ai_controller(self, ai_type, team, level_data):
        """根据AI类型创建AI控制器"""
        
        # 恶魔级AI（最高难度）
        if ai_type == "apocalypse":
            from demon_ai import ApocalypseAI
            return ApocalypseAI(team)
        elif ai_type == "nightmare":
            from demon_ai import NightmareAI
            return NightmareAI(team)
        elif ai_type == "demon":
            from demon_ai import DemonAI
            return DemonAI(team)
        
        # 空战专用AI
        elif ai_type == "kamikaze":
            from dogfight_ai import KamikazeAI
            return KamikazeAI(team)
        elif ai_type == "blitzkrieg":
            from dogfight_ai import BlitzkriegAI
            return BlitzkriegAI(team)
        elif ai_type == "dogfight":
            from dogfight_ai import DogfightAI
            return DogfightAI(team)
        
        # 精英级AI
        elif ai_type == "terminator":
            from super_ai import TerminatorAI
            return TerminatorAI(team)
        elif ai_type == "elite":
            from super_ai import EliteAI
            return EliteAI(team)
        
        # 改进AI系列
        elif ai_type == "hyper_aggressive":
            from improved_ai import HyperAggressiveAI
            return HyperAggressiveAI(team)
        elif ai_type == "turtle":
            from improved_ai import TurtleAI
            return TurtleAI(team)
        elif ai_type == "advanced":
            from improved_ai import AdvancedAI
            return AdvancedAI(team)
        
        # 基础AI系列
        elif ai_type == "aggressive":
            from ai import AggressiveAI
            return AggressiveAI(team)
        elif ai_type == "defensive":
            from ai import DefensiveAI
            return DefensiveAI(team)
        elif ai_type == "simple":
            from ai import SimpleAI
            return SimpleAI(team)
        
        # 默认使用高级AI
        else:
            from super_ai import EliteAI
            return EliteAI(team)
        
    def get_map_center(self, game_state):
        """计算地图中心点"""
        if not game_state.units:
            return 600, 400  # 默认中心
            
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for unit in game_state.units:
            min_x = min(min_x, unit.x)
            max_x = max(max_x, unit.x)
            min_y = min(min_y, unit.y)
            max_y = max(max_y, unit.y)
            
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        return center_x, center_y
        
    def load_level(self, level_index, game_state, sprite_manager):
        if level_index >= len(self.available_levels):
            return False
            
        level_info = self.available_levels[level_index]
        print(f"Loading level: {level_info['name']} with {level_info.get('ai_type', 'advanced')} AI")
        
        try:
            with open(level_info['path'], 'r', encoding='utf-8') as f:
                level_data = json.load(f)
                
            self.current_level_data = level_data
            game_state.units.clear()
            game_state.ai_controllers.clear()
            
            # 加载单位数据
            units_data = level_data.get("units", {})
            
            # 加载精灵
            sprites = level_data.get("sprites", {})
            for sprite_name, sprite_path in sprites.items():
                full_path = os.path.join(self.levels_folder, sprite_path)
                sprite_manager.load_sprite(sprite_name, full_path)
                
            # 加载背景
            background_path = level_data.get("background", None)
            if background_path:
                full_path = os.path.join(self.levels_folder, background_path)
                try:
                    game_state.background_image = pygame.image.load(full_path).convert()
                    print(f"Loaded background: {background_path}")
                except:
                    print(f"Failed to load background: {background_path}")
            
            # 加载玩家单位
            player_units_loaded = 0
            for unit_spawn in level_data.get("player_units", []):
                unit_type = unit_spawn["unit_id"]
                unit_data = units_data[unit_type]
                x, y = unit_spawn["position"]
                
                if unit_data["type"] == "repair":
                    unit = RepairUnit(x, y, 0, unit_data)
                else:
                    unit = Unit(x, y, 0, unit_data)
                game_state.add_unit(unit)
                player_units_loaded += 1
                
            # 加载敌方单位
            enemy_units_loaded = 0
            for unit_spawn in level_data.get("enemy_units", []):
                unit_type = unit_spawn["unit_id"]
                unit_data = units_data[unit_type]
                x, y = unit_spawn["position"]
                
                if unit_data["type"] == "repair":
                    unit = RepairUnit(x, y, 1, unit_data)
                else:
                    unit = Unit(x, y, 1, unit_data)
                game_state.add_unit(unit)
                enemy_units_loaded += 1
                
            # 创建AI控制器（支持多种AI类型）
            ai_type = level_data.get("ai_type", "advanced")
            ai_controller = self.get_ai_controller(ai_type, 1, level_data)
            game_state.ai_controllers.append(ai_controller)
            
            # 可选：支持多个AI控制器
            additional_ais = level_data.get("additional_ais", [])
            for ai_config in additional_ais:
                ai_type = ai_config.get("type", "advanced")
                ai_team = ai_config.get("team", 1)
                additional_ai = self.get_ai_controller(ai_type, ai_team, level_data)
                game_state.ai_controllers.append(additional_ai)
            
            print(f"Level loaded successfully:")
            print(f"  - Player units: {player_units_loaded}")
            print(f"  - Enemy units: {enemy_units_loaded}")
            print(f"  - AI controllers: {len(game_state.ai_controllers)}")
            print(f"  - AI type: {ai_type}")
            
            return True
            
        except Exception as e:
            print(f"Error loading level: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def check_victory(self, game_state):
        """检查胜利条件"""
        # 检查是否有自定义胜利条件
        if self.current_level_data:
            victory_conditions = self.current_level_data.get("victory_conditions", {})
            
            # 支持多种胜利条件
            if "eliminate_all" in victory_conditions and victory_conditions["eliminate_all"]:
                enemy_units = [u for u in game_state.units if u.team != game_state.player_team 
                              and u.state != UnitState.DEAD]
                if len(enemy_units) == 0:
                    return True
                    
            if "eliminate_mothership" in victory_conditions and victory_conditions["eliminate_mothership"]:
                enemy_mothership = game_state.get_mothership(1 - game_state.player_team)
                if not enemy_mothership or enemy_mothership.state == UnitState.DEAD:
                    return True
                    
            if "survive_time" in victory_conditions:
                # 这需要在游戏状态中追踪时间
                target_time = victory_conditions["survive_time"]
                current_time = getattr(game_state, 'level_time', 0)
                if current_time >= target_time:
                    return True
                    
            if "eliminate_specific" in victory_conditions:
                # 消灭特定类型的敌人
                target_types = victory_conditions["eliminate_specific"]
                for target_type in target_types:
                    enemy_units = [u for u in game_state.units 
                                  if (u.team != game_state.player_team and 
                                      u.state != UnitState.DEAD and
                                      u.unit_type.value == target_type)]
                    if len(enemy_units) > 0:
                        return False
                return True
        
        # 默认胜利条件：消灭所有敌人
        enemy_units = [u for u in game_state.units if u.team != game_state.player_team 
                       and u.state != UnitState.DEAD]
        return len(enemy_units) == 0
        
    def check_defeat(self, game_state):
        """检查失败条件"""
        # 检查是否有自定义失败条件
        if self.current_level_data:
            defeat_conditions = self.current_level_data.get("defeat_conditions", {})
            
            if "lose_all" in defeat_conditions and defeat_conditions["lose_all"]:
                player_units = [u for u in game_state.units if u.team == game_state.player_team 
                               and u.state != UnitState.DEAD]
                if len(player_units) == 0:
                    return True
                    
            if "lose_mothership" in defeat_conditions and defeat_conditions["lose_mothership"]:
                player_mothership = game_state.get_mothership(game_state.player_team)
                if not player_mothership or player_mothership.state == UnitState.DEAD:
                    return True
                    
            if "time_limit" in defeat_conditions:
                time_limit = defeat_conditions["time_limit"]
                current_time = getattr(game_state, 'level_time', 0)
                if current_time >= time_limit:
                    return True
        
        # 默认失败条件：玩家所有单位被消灭
        player_units = [u for u in game_state.units if u.team == game_state.player_team 
                        and u.state != UnitState.DEAD]
        return len(player_units) == 0
        
    def get_level_info(self, level_index):
        """获取关卡信息"""
        if level_index < len(self.available_levels):
            return self.available_levels[level_index]
        return None
        
    def get_level_count(self):
        """获取关卡数量"""
        return len(self.available_levels)
        
    def create_test_level(self, difficulty="normal"):
        """创建测试关卡"""
        test_level_data = {
            "name": f"测试关卡 ({difficulty})",
            "description": f"用于测试AI的{difficulty}难度关卡",
            "ai_type": "advanced" if difficulty == "normal" else "aggressive" if difficulty == "hard" else "simple",
            "difficulty": difficulty,
            "victory_conditions": {
                "eliminate_all": True
            },
            "defeat_conditions": {
                "lose_mothership": True
            },
            "units": {
                "player_mothership": {
                    "type": "mothership",
                    "name": "指挥舰",
                    "description": "玩家的主力舰",
                    "max_hp": 1000,
                    "speed": 50,
                    "attack_damage": 100,
                    "attack_range": 200,
                    "attack_cooldown": 2.0,
                    "radius": 40,
                    "attack_type": "beam"
                },
                "enemy_mothership": {
                    "type": "mothership", 
                    "name": "敌舰",
                    "description": "敌方主力舰",
                    "max_hp": 800,
                    "speed": 50,
                    "attack_damage": 80,
                    "attack_range": 180,
                    "attack_cooldown": 2.0,
                    "radius": 40,
                    "attack_type": "ranged"
                }
            },
            "player_units": [
                {"unit_id": "player_mothership", "position": [300, 400]}
            ],
            "enemy_units": [
                {"unit_id": "enemy_mothership", "position": [900, 400]}
            ]
        }
        
        return test_level_data