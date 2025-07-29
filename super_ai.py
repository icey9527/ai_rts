import math
import random
import time
from improved_ai import AdvancedAI
from units import UnitType, UnitState
from config import *

class EliteAI(AdvancedAI):
    """精英级AI - 极其强化的敌方AI"""
    
    def __init__(self, team):
        super().__init__(team)
        self.reaction_time = 0.05  # 极快反应
        self.micro_timer = 0
        self.formation_timer = 0
        self.tactical_memory = {}  # 战术记忆
        self.player_behavior_analysis = {
            'last_positions': [],
            'movement_patterns': {},
            'target_preferences': {},
            'retreat_threshold': 0.3
        }
        
    def update(self, units, game_state):
        self.command_cooldown -= 1/60
        self.strategy_timer += 1/60
        self.micro_timer += 1/60
        self.formation_timer += 1/60
        
        # 极高频率更新
        if self.command_cooldown > 0:
            return
            
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        player_mothership = game_state.get_mothership(1 - self.team)
        my_mothership = game_state.get_mothership(self.team)
        
        # 分析玩家行为模式
        self.analyze_player_behavior(enemy_units, game_state)
        
        # 极频繁的战术调整
        if self.strategy_timer > 1.0:
            self.advanced_strategy_adjustment(my_units, enemy_units, player_mothership)
            self.strategy_timer = 0
            
        # 超高频微操
        if self.micro_timer > 0.03:  # 33次/秒的微操
            self.elite_micro_management(my_units, enemy_units, game_state)
            self.micro_timer = 0
            
        # 编队控制
        if self.formation_timer > 0.5:
            self.advanced_formation_control(my_units, enemy_units, my_mothership)
            self.formation_timer = 0
            
        # 执行超级策略
        self.execute_elite_strategy(my_units, enemy_units, player_mothership, game_state)
        
        self.command_cooldown = 0.05  # 极高更新频率
        
    def analyze_player_behavior(self, enemy_units, game_state):
        """分析玩家行为模式"""
        player_mothership = game_state.get_mothership(1 - self.team)
        if not player_mothership:
            return
            
        # 记录玩家母舰位置
        current_pos = (player_mothership.x, player_mothership.y)
        self.player_behavior_analysis['last_positions'].append(current_pos)
        
        # 只保留最近20个位置
        if len(self.player_behavior_analysis['last_positions']) > 20:
            self.player_behavior_analysis['last_positions'].pop(0)
            
    def advanced_strategy_adjustment(self, my_units, enemy_units, player_mothership):
        """高级策略调整"""
        if not my_units or not enemy_units:
            return
            
        # 多因素综合分析
        my_strength = self.calculate_detailed_strength(my_units)
        enemy_strength = self.calculate_detailed_strength(enemy_units)
        
        # 综合决策
        strength_ratio = my_strength / max(enemy_strength, 1)
        
        if strength_ratio > 1.2:
            self.current_strategy = "overwhelming_assault"
        elif strength_ratio > 1.0:
            self.current_strategy = "coordinated_attack"
        elif strength_ratio < 0.8:
            self.current_strategy = "guerrilla_tactics"
        else:
            self.current_strategy = "adaptive_pressure"
            
    def calculate_detailed_strength(self, units):
        """详细实力计算"""
        total_strength = 0
        for unit in units:
            base_strength = unit.hp + unit.attack_damage * 3
            
            # 能量加成
            energy_ratio = unit.energy / unit.max_energy if unit.max_energy > 0 else 1
            base_strength *= (0.6 + energy_ratio * 0.4)
            
            # 技能加成
            if hasattr(unit, 'sp') and hasattr(unit, 'max_sp') and unit.max_sp > 0:
                if unit.sp >= unit.max_sp * 0.8:
                    base_strength *= 1.5
                    
            # 单位类型加权
            if unit.unit_type == UnitType.MOTHERSHIP:
                base_strength *= 4
            elif unit.unit_type == UnitType.HEAVY:
                base_strength *= 2
            elif unit.unit_type == UnitType.BOMBER:
                base_strength *= 1.8
                
            total_strength += base_strength
            
        return total_strength
        
    def elite_micro_management(self, my_units, enemy_units, game_state):
        """精英级微操管理"""
        for unit in my_units:
            if unit.unit_type == UnitType.MOTHERSHIP:
                self.mothership_elite_control(unit, my_units, enemy_units, game_state)
                continue
                
            # 超主动的能量管理
            if unit.energy < 40 and unit.state != UnitState.RETURNING:
                unit.state = UnitState.RETURNING
                continue
                
            # 超智能技能释放
            if self.should_use_skill_elite(unit, my_units + enemy_units, game_state):
                unit.use_skill(my_units + enemy_units, game_state)
                
            # 动态目标重新评估
            if unit.attack_target:
                better_target = self.find_better_target(unit, unit.attack_target, enemy_units, my_units)
                if better_target and better_target != unit.attack_target:
                    unit.attack_target = better_target
                    unit.target = better_target
                    unit.state = UnitState.ATTACKING
                    
    def mothership_elite_control(self, mothership, my_units, enemy_units, game_state):
        """母舰精英控制"""
        if enemy_units:
            target = self.select_mothership_target(mothership, enemy_units, my_units)
            if target and mothership.distance_to(target) <= mothership.attack_range:
                mothership.attack_target = target
                mothership.target = target
                mothership.state = UnitState.ATTACKING
                
    def should_use_skill_elite(self, unit, units, game_state):
        """精英级技能释放判断"""
        if not hasattr(unit, 'sp') or not hasattr(unit, 'max_sp') or unit.sp < unit.max_sp:
            return False
            
        if not hasattr(unit, 'skill_data') or not unit.skill_data:
            return False
            
        skill_type = unit.skill_data.get("type", "")
        skill_range = unit.skill_data.get("range", 100)
        
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if skill_type == "damage_aoe":
            enemies_in_range = [e for e in enemy_units if unit.distance_to(e) <= skill_range]
            return len(enemies_in_range) >= 2
            
        elif skill_type == "heal_aoe":
            damaged_allies = [a for a in my_units 
                            if (unit.distance_to(a) <= skill_range and 
                                a.hp < a.max_hp * 0.7)]
            return len(damaged_allies) >= 2
            
        elif skill_type in ["buff_speed", "buff_attack"]:
            nearby_enemies = [e for e in enemy_units if unit.distance_to(e) < 200]
            allies_nearby = [a for a in my_units if unit.distance_to(a) < skill_range and a != unit]
            return len(nearby_enemies) >= 1 and len(allies_nearby) >= 2
            
        elif skill_type == "shield":
            incoming_damage = self.calculate_incoming_damage(unit, enemy_units)
            return incoming_damage > unit.hp * 0.3
            
        return False
        
    def execute_elite_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """执行精英策略"""
        if self.current_strategy == "overwhelming_assault":
            self.overwhelming_assault(my_units, enemy_units, player_mothership, game_state)
        elif self.current_strategy == "coordinated_attack":
            self.coordinated_attack(my_units, enemy_units, player_mothership, game_state)
        elif self.current_strategy == "guerrilla_tactics":
            self.guerrilla_tactics(my_units, enemy_units, player_mothership, game_state)
        else:  # adaptive_pressure
            self.adaptive_pressure(my_units, enemy_units, player_mothership, game_state)
            
    def overwhelming_assault(self, my_units, enemy_units, player_mothership, game_state):
        """压倒性攻击"""
        for unit in my_units:
            if unit.unit_type == UnitType.MOTHERSHIP:
                continue
                
            if unit.energy < 20:
                continue
                
            target = self.select_best_target(unit, enemy_units, my_units)
            if target:
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
    def coordinated_attack(self, my_units, enemy_units, player_mothership, game_state):
        """协调攻击"""
        combat_units = [u for u in my_units if u.unit_type not in [UnitType.MOTHERSHIP, UnitType.REPAIR]]
        
        for i, unit in enumerate(combat_units):
            if unit.energy < 25:
                continue
                
            target = self.select_best_target(unit, enemy_units, my_units)
            if target:
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                    
    def guerrilla_tactics(self, my_units, enemy_units, player_mothership, game_state):
        """游击战术"""
        for unit in my_units:
            if unit.unit_type == UnitType.MOTHERSHIP:
                continue
                
            if unit.energy < 30:
                unit.state = UnitState.RETURNING
                continue
                
            # 优先攻击落单的敌人
            isolated_enemies = []
            for enemy in enemy_units:
                nearby_allies = [e for e in enemy_units if e != enemy and enemy.distance_to(e) < 150]
                if len(nearby_allies) <= 1:
                    isolated_enemies.append(enemy)
                    
            if isolated_enemies:
                target = min(isolated_enemies, key=lambda e: unit.distance_to(e))
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
            else:
                target = self.select_best_target(unit, enemy_units, my_units)
                if target:
                    unit.attack_target = target
                    unit.target = target
                    unit.state = UnitState.ATTACKING
                    
    def adaptive_pressure(self, my_units, enemy_units, player_mothership, game_state):
        """适应性压力"""
        combat_units = [u for u in my_units if u.unit_type not in [UnitType.MOTHERSHIP, UnitType.REPAIR]]
        
        for unit in combat_units:
            if unit.energy < 25:
                unit.state = UnitState.RETURNING
                continue
                
            target = self.select_best_target(unit, enemy_units, my_units)
            if target:
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
    def advanced_formation_control(self, my_units, enemy_units, my_mothership):
        """高级编队控制"""
        # 简化的编队控制
        pass
        
    def find_better_target(self, unit, current_target, enemy_units, my_units):
        """寻找更好的目标"""
        if not current_target:
            return self.select_best_target(unit, enemy_units, my_units)
            
        current_score = self.calculate_target_score(unit, current_target, my_units)
        best_target = current_target
        best_score = current_score
        
        for enemy in enemy_units:
            if enemy == current_target:
                continue
            score = self.calculate_target_score(unit, enemy, my_units)
            if score > best_score * 1.2:
                best_score = score
                best_target = enemy
                
        return best_target
        
    def calculate_target_score(self, unit, target, my_units):
        """计算目标分数"""
        distance = unit.distance_to(target)
        if distance > unit.attack_range * 3:
            return 0
            
        score = 0
        
        # 血量因素
        hp_ratio = target.hp / target.max_hp
        if hp_ratio < 0.3:
            score += 100
        elif hp_ratio < 0.6:
            score += 50
            
        # 距离因素
        score += max(0, 200 - distance) / 200 * 50
        
        # 威胁因素
        score += target.attack_damage * 2
        
        # 类型优先级
        if target.unit_type == UnitType.MOTHERSHIP:
            score += 200
        elif target.unit_type == UnitType.REPAIR:
            score += 150
        elif target.unit_type == UnitType.BOMBER:
            score += 100
            
        return score
        
    def calculate_incoming_damage(self, unit, enemy_units):
        """计算即将受到的伤害"""
        incoming_damage = 0
        for enemy in enemy_units:
            if (hasattr(enemy, 'attack_target') and enemy.attack_target == unit and 
                enemy.distance_to(unit) <= enemy.attack_range * 1.5):
                incoming_damage += enemy.attack_damage
        return incoming_damage
        
    def select_mothership_target(self, mothership, enemy_units, my_units):
        """为母舰选择目标"""
        enemies_in_range = [e for e in enemy_units 
                          if mothership.distance_to(e) <= mothership.attack_range]
        
        if not enemies_in_range:
            return None
            
        return max(enemies_in_range, 
                  key=lambda e: self.calculate_target_score(mothership, e, my_units))

class TerminatorAI(EliteAI):
    """终结者AI - 最强版本"""
    
    def __init__(self, team):
        super().__init__(team)
        self.terminator_mode = True
        
    def update(self, units, game_state):
        # 超高频更新
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"TERMINATOR MODE: {len(my_units)} units engaging {len(enemy_units)} targets")
        
        # 每个单位都要锁定目标
        for unit in my_units:
            self.terminator_control(unit, enemy_units, game_state)
            
    def terminator_control(self, unit, enemy_units, game_state):
        """终结者控制模式"""
        
        # 永不停歇的攻击
        if unit.energy >= 1:  # 只要有一点能量就继续战斗
            
            # 强制使用技能
            if (hasattr(unit, 'sp') and hasattr(unit, 'max_sp') and 
                unit.sp >= unit.max_sp * 0.5):  # 50%就释放技能
                unit.use_skill(enemy_units + [unit], game_state)
                
            # 选择目标
            target = self.select_terminator_target(unit, enemy_units)
            
            if target:
                print(f"TERMINATOR {unit.unit_type}: TARGET ACQUIRED - {target.unit_type}")
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
        else:
            # 能量耗尽才回去
            unit.state = UnitState.RETURNING
            
    def select_terminator_target(self, unit, enemy_units):
        """终结者目标选择"""
        if not enemy_units:
            return None
            
        # 按威胁等级排序
        def threat_level(enemy):
            threat = 0
            
            # 母舰威胁最高
            if enemy.unit_type == UnitType.MOTHERSHIP:
                threat += 10000
            # 修理机第二威胁
            elif enemy.unit_type == UnitType.REPAIR:
                threat += 5000
            # 其他按攻击力
            else:
                threat += enemy.attack_damage * 10
                
            # 残血加成
            if enemy.hp < enemy.max_hp * 0.5:
                threat += 1000
                
            # 距离因素（近的威胁大）
            distance = unit.distance_to(enemy)
            threat += max(0, 2000 - distance)
            
            return threat
            
        return max(enemy_units, key=threat_level)