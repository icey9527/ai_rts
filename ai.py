from abc import ABC, abstractmethod
from units import UnitType, UnitState
import random
import math

class AIController(ABC):
    def __init__(self, team):
        self.team = team
        
    @abstractmethod
    def update(self, units, game_state):
        pass

class SimpleAI(AIController):
    def __init__(self, team):
        super().__init__(team)
        self.command_cooldown = 0
        self.strategy_timer = 0
        self.current_strategy = "aggressive"  # aggressive, defensive, balanced
        self.last_player_mothership_pos = None
        self.attack_waves = []  # 攻击波次
        self.formation_center = None
        
    def update(self, units, game_state):
        self.command_cooldown -= 1/60  # 假设60 FPS
        self.strategy_timer += 1/60
        
        if self.command_cooldown > 0:
            return
            
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        player_mothership = game_state.get_mothership(1 - self.team)
        
        # 每5秒调整策略
        if self.strategy_timer > 5.0:
            self.adjust_strategy(my_units, enemy_units)
            self.strategy_timer = 0
            
        # 执行策略
        if self.current_strategy == "aggressive":
            self.execute_aggressive_strategy(my_units, enemy_units, player_mothership, game_state)
        elif self.current_strategy == "defensive":
            self.execute_defensive_strategy(my_units, enemy_units, player_mothership, game_state)
        else:
            self.execute_balanced_strategy(my_units, enemy_units, player_mothership, game_state)
            
        self.command_cooldown = 0.3  # 每0.3秒更新一次命令
        
    def adjust_strategy(self, my_units, enemy_units):
        """根据战场情况调整策略"""
        my_strength = sum(u.hp + u.attack_damage for u in my_units)
        enemy_strength = sum(u.hp + u.attack_damage for u in enemy_units)
        
        strength_ratio = my_strength / max(enemy_strength, 1)
        
        if strength_ratio > 1.3:
            self.current_strategy = "aggressive"
        elif strength_ratio < 0.7:
            self.current_strategy = "defensive" 
        else:
            self.current_strategy = "balanced"
            
        print(f"AI Strategy: {self.current_strategy} (Ratio: {strength_ratio:.2f})")
        
    def execute_aggressive_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """激进策略：全力进攻"""
        # 优先攻击玩家母舰
        if player_mothership:
            for unit in my_units:
                if unit.unit_type == UnitType.MOTHERSHIP:
                    continue
                    
                # 如果单位没有目标或者目标不是母舰，就攻击母舰
                if (not hasattr(unit, 'attack_target') or 
                    unit.attack_target != player_mothership or
                    unit.state == UnitState.IDLE):
                    
                    unit.attack_target = player_mothership
                    unit.target = player_mothership
                    unit.state = UnitState.ATTACKING
                    
        # 母舰提供火力支援
        mothership = game_state.get_mothership(self.team)
        if mothership and enemy_units:
            nearest_enemy = min(enemy_units, key=lambda u: mothership.distance_to(u))
            if mothership.distance_to(nearest_enemy) <= mothership.attack_range:
                mothership.target = nearest_enemy
                mothership.attack_target = nearest_enemy
                mothership.state = UnitState.ATTACKING
                
    def execute_defensive_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """防守策略：保护母舰"""
        mothership = game_state.get_mothership(self.team)
        if not mothership:
            return
            
        # 所有单位围绕母舰防守
        for unit in my_units:
            if unit.unit_type == UnitType.MOTHERSHIP:
                continue
                
            # 能量低时返回母舰
            if unit.energy < 30:
                unit.state = UnitState.RETURNING
                continue
                
            # 在母舰附近寻找敌人
            nearby_enemies = [e for e in enemy_units 
                            if mothership.distance_to(e) < 300]
                            
            if nearby_enemies:
                # 攻击最近的敌人
                target = min(nearby_enemies, key=lambda u: unit.distance_to(u))
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
            else:
                # 在母舰周围巡逻
                patrol_radius = 150
                angle = random.random() * 2 * math.pi
                patrol_x = mothership.x + math.cos(angle) * patrol_radius
                patrol_y = mothership.y + math.sin(angle) * patrol_radius
                
                unit.target_pos = (patrol_x, patrol_y)
                unit.state = UnitState.MOVING
                
    def execute_balanced_strategy(self, my_units, enemy_units, player_mothership, game_state):
        """平衡策略：攻守兼备"""
        mothership = game_state.get_mothership(self.team)
        combat_units = [u for u in my_units if u.unit_type != UnitType.MOTHERSHIP and u.unit_type != UnitType.REPAIR]
        repair_units = [u for u in my_units if u.unit_type == UnitType.REPAIR]
        
        # 分配一半单位进攻，一半防守
        attack_units = combat_units[:len(combat_units)//2]
        defense_units = combat_units[len(combat_units)//2:]
        
        # 进攻单位：攻击最近的敌人
        for unit in attack_units:
            if unit.energy < 20:
                unit.state = UnitState.RETURNING
                continue
                
            if enemy_units:
                # 优先攻击血量低的敌人
                damaged_enemies = [e for e in enemy_units if e.hp < e.max_hp * 0.5]
                if damaged_enemies:
                    target = min(damaged_enemies, key=lambda u: unit.distance_to(u))
                else:
                    target = min(enemy_units, key=lambda u: unit.distance_to(u))
                    
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
        # 防守单位：保护母舰和修理机
        for unit in defense_units:
            if unit.energy < 30:
                unit.state = UnitState.RETURNING
                continue
                
            # 寻找威胁母舰的敌人
            threats = [e for e in enemy_units 
                      if mothership and mothership.distance_to(e) < 250]
                      
            if threats:
                target = min(threats, key=lambda u: unit.distance_to(u))
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
            else:
                # 跟随母舰
                if mothership:
                    unit.follow_target = mothership
                    unit.state = UnitState.FOLLOWING
                    
        # 修理机逻辑
        for repair_unit in repair_units:
            if repair_unit.energy < 20:
                repair_unit.state = UnitState.RETURNING
                continue
                
            # 寻找需要修理的单位
            damaged_allies = [u for u in my_units 
                            if u.hp < u.max_hp * 0.7 and u != repair_unit]
            if damaged_allies:
                # 优先修理血量最低的
                target = min(damaged_allies, key=lambda u: u.hp / u.max_hp)
                repair_unit.repair_target = target
                repair_unit.target = target
                repair_unit.state = UnitState.REPAIRING
            else:
                # 跟随母舰
                if mothership:
                    repair_unit.follow_target = mothership
                    repair_unit.state = UnitState.FOLLOWING
                    
        # 母舰AI：使用技能和攻击
        if mothership:
            # 使用技能
            if hasattr(mothership, 'sp') and mothership.sp >= mothership.max_sp:
                mothership.use_skill(my_units + enemy_units, game_state)
                
            # 攻击范围内的敌人
            if enemy_units:
                enemies_in_range = [e for e in enemy_units 
                                  if mothership.distance_to(e) <= mothership.attack_range]
                if enemies_in_range:
                    # 优先攻击血量低的敌人
                    target = min(enemies_in_range, key=lambda u: u.hp)
                    mothership.attack_target = target
                    mothership.target = target
                    mothership.state = UnitState.ATTACKING
                    
        # 使用技能
        for unit in my_units:
            if (hasattr(unit, 'sp') and unit.sp >= unit.max_sp and 
                unit.unit_type != UnitType.MOTHERSHIP):
                unit.use_skill(my_units + enemy_units, game_state)

class AggressiveAI(SimpleAI):
    """更激进的AI"""
    def __init__(self, team):
        super().__init__(team)
        self.current_strategy = "aggressive"
        
    def adjust_strategy(self, my_units, enemy_units):
        # 始终保持激进
        self.current_strategy = "aggressive"

class DefensiveAI(SimpleAI):
    """防守型AI"""
    def __init__(self, team):
        super().__init__(team)
        self.current_strategy = "defensive"
        
    def adjust_strategy(self, my_units, enemy_units):
        # 始终保持防守
        self.current_strategy = "defensive"