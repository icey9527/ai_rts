import math
import random
import time
from abc import ABC, abstractmethod
from units import UnitType, UnitState
from config import *

class ImprovedAIController(ABC):
    def __init__(self, team):
        self.team = team
        self.command_cooldown = 0
        self.strategy_timer = 0
        self.last_strategy_change = 0
        self.target_priorities = {}  # 目标优先级缓存
        self.group_formations = {}   # 编队信息
        self.last_threat_assessment = 0
        self.threat_map = {}
        
    @abstractmethod
    def update(self, units, game_state):
        pass
    
    def assess_threats(self, my_units, enemy_units):
        """威胁评估系统"""
        current_time = time.time()
        if current_time - self.last_threat_assessment < 1.0:  # 每秒评估一次
            return self.threat_map
            
        self.threat_map.clear()
        self.last_threat_assessment = current_time
        
        for enemy in enemy_units:
            # 计算威胁值
            threat_score = 0
            
            # 基础威胁（攻击力和血量）
            threat_score += enemy.attack_damage * 2
            threat_score += enemy.hp * 0.5
            
            # 距离威胁（距离我方单位越近威胁越大）
            min_distance = float('inf')
            for my_unit in my_units:
                dist = enemy.distance_to(my_unit)
                if dist < min_distance:
                    min_distance = dist
            
            if min_distance < 200:
                threat_score *= 2
            elif min_distance < 400:
                threat_score *= 1.5
                
            # 特殊单位威胁加成
            if enemy.unit_type == UnitType.MOTHERSHIP:
                threat_score *= 3
            elif enemy.unit_type == UnitType.BOMBER:
                threat_score *= 2
            elif enemy.unit_type == UnitType.HEAVY:
                threat_score *= 1.5
                
            self.threat_map[enemy] = threat_score
            
        return self.threat_map
    
    def select_best_target(self, unit, enemy_units, my_units):
        """智能目标选择"""
        if not enemy_units:
            return None
            
        threat_map = self.assess_threats(my_units, enemy_units)
        best_target = None
        best_score = -1
        
        for enemy in enemy_units:
            distance = unit.distance_to(enemy)
            
            # 超出攻击范围的目标降低优先级
            if distance > unit.attack_range * 2:
                continue
                
            score = 0
            
            # 威胁值权重
            threat_score = threat_map.get(enemy, 0)
            score += threat_score * 0.4
            
            # 距离权重（越近越好）
            distance_score = max(0, 500 - distance) / 500 * 100
            score += distance_score * 0.3
            
            # 血量权重（优先攻击残血）
            hp_ratio = enemy.hp / enemy.max_hp
            if hp_ratio < 0.3:
                score += 100  # 残血目标高优先级
            elif hp_ratio < 0.6:
                score += 50
                
            # 单位类型优先级
            if enemy.unit_type == UnitType.MOTHERSHIP:
                score += 200
            elif enemy.unit_type == UnitType.REPAIR:
                score += 150  # 优先攻击修理机
            elif enemy.unit_type == UnitType.BOMBER:
                score += 120
                
            # 是否在攻击范围内
            if distance <= unit.attack_range:
                score += 100
                
            if score > best_score:
                best_score = score
                best_target = enemy
                
        return best_target
    
    def should_use_skill(self, unit, units, game_state):
        """智能技能释放判断"""
        if unit.sp < unit.max_sp or not unit.skill_data:
            return False
            
        # 获取技能信息
        skill_type = unit.skill_data.get("type", "")
        skill_range = unit.skill_data.get("range", 100)
        
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if skill_type == "damage_aoe":
            # 范围伤害：检查范围内敌人数量
            enemies_in_range = 0
            for enemy in enemy_units:
                if unit.distance_to(enemy) <= skill_range:
                    enemies_in_range += 1
            return enemies_in_range >= 2  # 至少2个敌人时释放
            
        elif skill_type == "heal_aoe":
            # 范围治疗：检查范围内受伤友军
            damaged_allies = 0
            for ally in my_units:
                if (unit.distance_to(ally) <= skill_range and 
                    ally.hp < ally.max_hp * 0.7):
                    damaged_allies += 1
            return damaged_allies >= 2
            
        elif skill_type in ["buff_speed", "buff_attack"]:
            # 增益技能：在战斗中释放
            nearby_enemies = [e for e in enemy_units if unit.distance_to(e) < 300]
            return len(nearby_enemies) >= 1
            
        elif skill_type == "shield":
            # 护盾：血量低时释放
            return unit.hp < unit.max_hp * 0.5
            
        elif skill_type == "disable":
            # 禁用：对威胁最大的敌人释放
            if enemy_units:
                threat_map = self.assess_threats(my_units, enemy_units)
                max_threat = max(threat_map.values()) if threat_map else 0
                return max_threat > 100
                
        return False

class AdvancedAI(ImprovedAIController):
    def __init__(self, team):
        super().__init__(team)
        self.current_strategy = "balanced"
        self.formations = {
            "defensive": {"formation_radius": 150, "max_distance": 200},
            "aggressive": {"formation_radius": 100, "max_distance": 300},
            "balanced": {"formation_radius": 120, "max_distance": 250}
        }
        self.micro_management_timer = 0
        
    def update(self, units, game_state):
        self.command_cooldown -= 1/60
        self.strategy_timer += 1/60
        self.micro_management_timer += 1/60
        
        if self.command_cooldown > 0:
            return
            
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        player_mothership = game_state.get_mothership(1 - self.team)
        my_mothership = game_state.get_mothership(self.team)
        
        # 每3秒调整策略
        if self.strategy_timer > 3.0:
            self.adjust_strategy(my_units, enemy_units, player_mothership)
            self.strategy_timer = 0
            
        # 每0.1秒进行微操
        if self.micro_management_timer > 0.1:
            self.micro_management(my_units, enemy_units, game_state)
            self.micro_management_timer = 0
            
        # 执行策略
        if self.current_strategy == "aggressive":
            self.execute_aggressive_strategy(my_units, enemy_units, player_mothership, game_state)
        elif self.current_strategy == "defensive":
            self.execute_defensive_strategy(my_units, enemy_units, player_mothership, game_state)
        else:
            self.execute_balanced_strategy(my_units, enemy_units, player_mothership, game_state)
            
        self.command_cooldown = 0.2  # 更频繁的命令更新
        
    def adjust_strategy(self, my_units, enemy_units, player_mothership):
        """动态策略调整"""
        if not my_units or not enemy_units:
            return
            
        # 计算综合实力对比
        my_strength = self.calculate_force_strength(my_units)
        enemy_strength = self.calculate_force_strength(enemy_units)
        
        strength_ratio = my_strength / max(enemy_strength, 1)
        
        # 考虑距离因素
        avg_distance = sum(u.distance_to(player_mothership) for u in my_units if player_mothership) / len(my_units) if player_mothership else 500
        
        # 策略决策
        if strength_ratio > 1.4 or (strength_ratio > 1.1 and avg_distance < 200):
            new_strategy = "aggressive"
        elif strength_ratio < 0.6 or avg_distance > 400:
            new_strategy = "defensive"
        else:
            new_strategy = "balanced"
            
        if new_strategy != self.current_strategy:
            self.current_strategy = new_strategy
            print(f"AI Strategy changed to: {self.current_strategy} (Ratio: {strength_ratio:.2f})")
            
    def calculate_force_strength(self, units):
        """计算部队综合实力"""
        strength = 0
        for unit in units:
            # 基础实力
            unit_strength = unit.hp + unit.attack_damage * 2
            
            # 能量影响
            energy_ratio = unit.energy / unit.max_energy if unit.max_energy > 0 else 1
            unit_strength *= (0.5 + energy_ratio * 0.5)
            
            # 单位类型加权
            if unit.unit_type == UnitType.MOTHERSHIP:
                unit_strength *= 3
            elif unit.unit_type == UnitType.HEAVY:
                unit_strength *= 1.5
            elif unit.unit_type == UnitType.BOMBER:
                unit_strength *= 1.3
                
            strength += unit_strength
            
        return strength
        
    def micro_management(self, my_units, enemy_units, game_state):
        """微操管理"""
        for unit in my_units:
            if unit.unit_type == UnitType.MOTHERSHIP:
                continue
                
            # 能量管理
            if unit.energy < 20 and unit.state != UnitState.RETURNING:
                unit.state = UnitState.RETURNING
                continue
                
            # 智能技能释放
            if self.should_use_skill(unit, my_units + enemy_units, game_state):
                unit.use_skill(my_units + enemy_units, game_state)
                
            # 修理机特殊逻辑
            if unit.unit_type == UnitType.REPAIR:
                self.manage_repair_unit(unit, my_units, enemy_units)
                
    def manage_repair_unit(self, repair_unit, my_units, enemy_units):
        """修理机管理"""
        if repair_unit.state == UnitState.RETURNING:
            return
            
        # 寻找最需要修理的单位
        damaged_allies = [u for u in my_units 
                         if (u != repair_unit and 
                             u.hp < u.max_hp * 0.8 and
                             repair_unit.distance_to(u) < 300)]
        
        if damaged_allies:
            # 按血量比例和重要性排序
            def repair_priority(unit):
                hp_ratio = unit.hp / unit.max_hp
                importance = 3 if unit.unit_type == UnitType.MOTHERSHIP else 1
                distance = repair_unit.distance_to(unit)
                return -(hp_ratio * 100 + importance * 100 - distance * 0.1)
                
            damaged_allies.sort(key=repair_priority)
            target = damaged_allies[0]
            
            if repair_unit.repair_target != target:
                repair_unit.repair_target = target
                repair_unit.target = target
                repair_unit.state = UnitState.REPAIRING
                
    def execute_aggressive_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """激进策略"""
        combat_units = [u for u in my_units if u.unit_type not in [UnitType.MOTHERSHIP, UnitType.REPAIR]]
        
        for unit in combat_units:
            if unit.energy < 30:
                continue
                
            # 选择最佳目标
            target = self.select_best_target(unit, enemy_units, my_units)
            if target:
                if (unit.attack_target != target or 
                    unit.state not in [UnitState.ATTACKING, UnitState.CIRCLE_STRAFING]):
                    unit.attack_target = target
                    unit.target = target
                    unit.state = UnitState.ATTACKING
                    
        # 母舰支援
        mothership = game_state.get_mothership(self.team)
        if mothership and enemy_units:
            target = self.select_best_target(mothership, enemy_units, my_units)
            if target and mothership.distance_to(target) <= mothership.attack_range:
                mothership.attack_target = target
                mothership.target = target
                mothership.state = UnitState.ATTACKING
                
    def execute_defensive_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """防守策略"""
        mothership = game_state.get_mothership(self.team)
        if not mothership:
            return
            
        formation_radius = self.formations["defensive"]["formation_radius"]
        max_distance = self.formations["defensive"]["max_distance"]
        
        combat_units = [u for u in my_units if u.unit_type not in [UnitType.MOTHERSHIP, UnitType.REPAIR]]
        
        for unit in combat_units:
            if unit.energy < 20:
                unit.state = UnitState.RETURNING
                continue
                
            distance_to_mothership = unit.distance_to(mothership)
            
            # 在防御圈内寻找目标
            nearby_enemies = [e for e in enemy_units 
                            if mothership.distance_to(e) < max_distance]
            
            if nearby_enemies:
                target = self.select_best_target(unit, nearby_enemies, my_units)
                if target:
                    unit.attack_target = target
                    unit.target = target
                    unit.state = UnitState.ATTACKING
            else:
                # 回到防御阵型
                if distance_to_mothership > formation_radius:
                    angle = random.random() * 2 * math.pi
                    pos_x = mothership.x + math.cos(angle) * formation_radius * 0.8
                    pos_y = mothership.y + math.sin(angle) * formation_radius * 0.8
                    
                    unit.target_pos = (pos_x, pos_y)
                    unit.state = UnitState.MOVING
                    
    def execute_balanced_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """平衡策略"""
        combat_units = [u for u in my_units if u.unit_type not in [UnitType.MOTHERSHIP, UnitType.REPAIR]]
        
        # 分配单位：60%进攻，40%防守
        attack_count = int(len(combat_units) * 0.6)
        attack_units = combat_units[:attack_count]
        defense_units = combat_units[attack_count:]
        
        # 进攻单位
        for unit in attack_units:
            if unit.energy < 25:
                unit.state = UnitState.RETURNING
                continue
                
            target = self.select_best_target(unit, enemy_units, my_units)
            if target:
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
        # 防守单位
        mothership = game_state.get_mothership(self.team)
        if mothership:
            for unit in defense_units:
                if unit.energy < 30:
                    unit.state = UnitState.RETURNING
                    continue
                    
                # 保护母舰
                threats = [e for e in enemy_units 
                          if mothership.distance_to(e) < 250]
                          
                if threats:
                    target = self.select_best_target(unit, threats, my_units)
                    if target:
                        unit.attack_target = target
                        unit.target = target
                        unit.state = UnitState.ATTACKING
                else:
                    # 巡逻
                    if unit.distance_to(mothership) > 200:
                        unit.follow_target = mothership
                        unit.state = UnitState.FOLLOWING

# 专门的激进AI
class HyperAggressiveAI(AdvancedAI):
    def __init__(self, team):
        super().__init__(team)
        self.current_strategy = "aggressive"
        
    def adjust_strategy(self, my_units, enemy_units, player_mothership):
        # 始终保持激进，但根据实力调整激进程度
        my_strength = self.calculate_force_strength(my_units)
        enemy_strength = self.calculate_force_strength(enemy_units)
        strength_ratio = my_strength / max(enemy_strength, 1)
        
        if strength_ratio > 0.8:
            self.current_strategy = "aggressive"
        else:
            self.current_strategy = "balanced"  # 实力不足时稍微保守

# 专门的防守AI
class TurtleAI(AdvancedAI):
    def __init__(self, team):
        super().__init__(team)
        self.current_strategy = "defensive"
        
    def adjust_strategy(self, my_units, enemy_units, player_mothership):
        # 始终保持防守，但实力足够时可以反击
        my_strength = self.calculate_force_strength(my_units)
        enemy_strength = self.calculate_force_strength(enemy_units)
        strength_ratio = my_strength / max(enemy_strength, 1)
        
        if strength_ratio > 1.5:
            self.current_strategy = "balanced"  # 实力碾压时主动出击
        else:
            self.current_strategy = "defensive"