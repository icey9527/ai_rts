import math
import random
import time
from super_ai import TerminatorAI
from units import UnitType, UnitState
from config import *

class DogfightAI(TerminatorAI):
    """空战AI - 专门用于高速战斗机对决"""
    
    def __init__(self, team):
        super().__init__(team)
        self.dogfight_mode = True
        self.engagement_range = 9999  # 无限交战距离
        self.last_enemy_positions = {}
        
    def update(self, units, game_state):
        # 超高频更新
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"DOGFIGHT AI: {len(my_units)} fighters vs {len(enemy_units)} enemies")
        
        # 记录敌人位置用于预判
        for enemy in enemy_units:
            self.last_enemy_positions[enemy] = (enemy.x, enemy.y, time.time())
        
        # 每个单位都要立即交战
        for unit in my_units:
            self.dogfight_control(unit, enemy_units, game_state)
            
    def dogfight_control(self, unit, enemy_units, game_state):
        """空战控制"""
        
        # 只要有一点能量就继续战斗
        if unit.energy < 1:
            unit.state = UnitState.RETURNING
            return
            
        # 非常激进的技能释放
        if unit.sp >= unit.max_sp * 0.3:  # 30%就释放技能！
            print(f"Fighter {unit.name} using skill at 30% SP!")
            unit.use_skill(enemy_units + [unit], game_state)
            
        # 选择目标并立即开火
        target = self.select_dogfight_target(unit, enemy_units)
        
        if target:
            distance = unit.distance_to(target)
            print(f"Fighter {unit.name} engaging {target.name} at {distance:.1f} units")
            
            # 无条件锁定并攻击
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING
            
            # 如果距离太远，强制移动过去
            if distance > unit.attack_range * 1.5:
                # 预判敌人位置
                predicted_pos = self.predict_enemy_position(target)
                unit.target_pos = predicted_pos
                print(f"Moving to intercept at predicted position: {predicted_pos}")
                
    def select_dogfight_target(self, unit, enemy_units):
        """空战目标选择 - 优先最近的敌人"""
        if not enemy_units:
            return None
            
        # 计算威胁值
        def calculate_threat(enemy):
            distance = unit.distance_to(enemy)
            
            # 基础威胁值
            threat = 1000
            
            # 距离越近威胁越大
            threat += max(0, 500 - distance)
            
            # 血量因素
            hp_ratio = enemy.hp / enemy.max_hp
            if hp_ratio < 0.4:
                threat += 300  # 残血优先
                
            # 攻击力威胁
            threat += enemy.attack_damage * 5
            
            # 速度威胁（快的敌人更危险）
            threat += enemy.speed * 2
            
            return threat
            
        return max(enemy_units, key=calculate_threat)
        
    def predict_enemy_position(self, enemy):
        """预判敌人位置"""
        if enemy not in self.last_enemy_positions:
            return (enemy.x, enemy.y)
            
        last_pos = self.last_enemy_positions[enemy]
        last_x, last_y, last_time = last_pos
        
        current_time = time.time()
        time_diff = current_time - last_time
        
        if time_diff > 0:
            # 计算速度向量
            vel_x = (enemy.x - last_x) / time_diff
            vel_y = (enemy.y - last_y) / time_diff
            
            # 预测0.5秒后的位置
            predict_time = 0.5
            predicted_x = enemy.x + vel_x * predict_time
            predicted_y = enemy.y + vel_y * predict_time
            
            return (predicted_x, predicted_y)
            
        return (enemy.x, enemy.y)

class BlitzkriegAI(DogfightAI):
    """闪电战AI - 极速攻击"""
    
    def __init__(self, team):
        super().__init__(team)
        self.blitz_mode = True
        
    def update(self, units, game_state):
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"BLITZKRIEG: All units charge!")
        
        # 所有单位同时冲锋
        for unit in my_units:
            self.blitzkrieg_charge(unit, enemy_units, game_state)
            
    def blitzkrieg_charge(self, unit, enemy_units, game_state):
        """闪电战冲锋"""
        
        # 永不停歇
        if unit.energy < 0.5:  # 几乎没能量才停
            unit.state = UnitState.RETURNING
            return
            
        # 立即释放技能
        if unit.sp >= unit.max_sp * 0.2:  # 20%就释放！
            unit.use_skill(enemy_units + [unit], game_state)
            
        # 找最近的敌人，直接冲过去
        if enemy_units:
            target = min(enemy_units, key=lambda e: unit.distance_to(e))
            
            print(f"BLITZ CHARGE: {unit.name} -> {target.name}")
            
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING
            
            # 强制移动到目标位置
            unit.target_pos = (target.x, target.y)

class KamikazeAI(BlitzkriegAI):
    """神风AI - 不计代价的攻击"""
    
    def __init__(self, team):
        super().__init__(team)
        self.kamikaze_mode = True
        
    def update(self, units, game_state):
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"KAMIKAZE MODE: {len(my_units)} units on suicide mission!")
        
        for unit in my_units:
            self.kamikaze_attack(unit, enemy_units, game_state)
            
    def kamikaze_attack(self, unit, enemy_units, game_state):
        """神风攻击 - 不计代价"""
        
        # 永不回头！即使没能量也要战斗
        if unit.energy <= 0 and unit.hp < unit.max_hp * 0.1:
            # 只有在濒死且没能量时才回去
            unit.state = UnitState.RETURNING
            return
            
        # 有一点SP就释放
        if unit.sp >= unit.max_sp * 0.1:  # 10%就释放技能！
            unit.use_skill(enemy_units + [unit], game_state)
            
        # 选择最高价值目标，不惜一切代价攻击
        if enemy_units:
            # 优先攻击血量最多的敌人（造成最大损失）
            target = max(enemy_units, key=lambda e: e.hp + e.attack_damage)
            
            print(f"KAMIKAZE: {unit.name} targeting {target.name} (HP: {target.hp})")
            
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING