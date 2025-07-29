import math
import random
import time
from super_ai import TerminatorAI
from units import UnitType, UnitState
from config import *

class DemonAI(TerminatorAI):
    """恶魔AI - 超级魔鬼级难度"""
    
    def __init__(self, team):
        super().__init__(team)
        self.demon_mode = True
        self.prediction_system = {}
        self.tactical_memory = []
        self.aggression_level = 10  # 最高侵略性
        self.last_player_positions = {}
        self.formation_tactics = "swarm"
        
    def update(self, units, game_state):
        # 疯狂高频更新
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"DEMON AI: {len(my_units)} demons hunting {len(enemy_units)} targets")
        
        # 记录和预测玩家行为
        self.analyze_and_predict_player_behavior(enemy_units)
        
        # 每个单位都是恶魔
        for unit in my_units:
            self.demon_control(unit, enemy_units, game_state)
            
    def analyze_and_predict_player_behavior(self, enemy_units):
        """分析和预测玩家行为"""
        current_time = time.time()
        
        for enemy in enemy_units:
            enemy_id = id(enemy)
            current_pos = (enemy.x, enemy.y)
            
            if enemy_id not in self.last_player_positions:
                self.last_player_positions[enemy_id] = []
                
            self.last_player_positions[enemy_id].append((current_pos, current_time))
            
            # 只保留最近的10个位置
            if len(self.last_player_positions[enemy_id]) > 10:
                self.last_player_positions[enemy_id].pop(0)
                
    def predict_enemy_future_position(self, enemy, predict_time=1.0):
        """预测敌人未来位置"""
        enemy_id = id(enemy)
        
        if (enemy_id not in self.last_player_positions or 
            len(self.last_player_positions[enemy_id]) < 3):
            return (enemy.x, enemy.y)
            
        positions = self.last_player_positions[enemy_id]
        
        # 计算平均速度向量
        total_vx = 0
        total_vy = 0
        valid_samples = 0
        
        for i in range(len(positions) - 1):
            (x1, y1), t1 = positions[i]
            (x2, y2), t2 = positions[i + 1]
            
            dt = t2 - t1
            if dt > 0:
                vx = (x2 - x1) / dt
                vy = (y2 - y1) / dt
                total_vx += vx
                total_vy += vy
                valid_samples += 1
                
        if valid_samples > 0:
            avg_vx = total_vx / valid_samples
            avg_vy = total_vy / valid_samples
            
            # 预测未来位置
            future_x = enemy.x + avg_vx * predict_time
            future_y = enemy.y + avg_vy * predict_time
            
            return (future_x, future_y)
            
        return (enemy.x, enemy.y)
        
    def demon_control(self, unit, enemy_units, game_state):
        """恶魔控制模式"""
        
        # 恶魔永不退缩！
        if unit.energy <= 0:
            # 即使没能量也要战斗到最后一滴血
            if unit.hp > unit.max_hp * 0.1:
                print(f"DEMON {unit.unit_type}: Fighting on empty energy!")
            else:
                unit.state = UnitState.RETURNING
                return
                
        # 疯狂释放技能
        if unit.sp >= unit.max_sp * 0.15:  # 15%就释放技能！
            print(f"DEMON {unit.unit_type}: Unleashing dark magic!")
            unit.use_skill(enemy_units + [unit], game_state)
            
        # 选择猎物
        target = self.select_demon_target(unit, enemy_units)
        
        if target:
            # 预测目标位置进行拦截
            predicted_pos = self.predict_enemy_future_position(target, 0.8)
            distance_to_current = unit.distance_to(target)
            distance_to_predicted = math.sqrt((unit.x - predicted_pos[0])**2 + (unit.y - predicted_pos[1])**2)
            
            print(f"DEMON {unit.unit_type}: Hunting {target.unit_type} (Current: {distance_to_current:.1f}, Predicted: {distance_to_predicted:.1f})")
            
            # 设置攻击目标
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING
            
            # 如果预测位置更好，移动到预测位置拦截
            if distance_to_predicted < distance_to_current:
                unit.target_pos = predicted_pos
                print(f"DEMON {unit.unit_type}: Intercepting at predicted position!")
                
    def select_demon_target(self, unit, enemy_units):
        """恶魔目标选择 - 极其智能和恶毒"""
        if not enemy_units:
            return None
            
        def demon_threat_calculation(enemy):
            threat_score = 0
            
            # 基础威胁
            threat_score += enemy.attack_damage * 20
            threat_score += enemy.hp * 5
            
            # 距离因素 - 恶魔喜欢近距离猎杀
            distance = unit.distance_to(enemy)
            if distance < 200:
                threat_score += 500
            elif distance < 400:
                threat_score += 300
            else:
                threat_score += max(0, 1000 - distance)
                
            # 血量状态 - 恶魔优先攻击受伤的猎物
            hp_ratio = enemy.hp / enemy.max_hp
            if hp_ratio < 0.3:
                threat_score += 800  # 残血目标极高优先级
            elif hp_ratio < 0.6:
                threat_score += 400
                
            # 能量状态 - 攻击能量低的目标
            if hasattr(enemy, 'energy') and enemy.max_energy > 0:
                energy_ratio = enemy.energy / enemy.max_energy
                if energy_ratio < 0.3:
                    threat_score += 300
                    
            # 单位类型威胁
            if enemy.unit_type == UnitType.MOTHERSHIP:
                threat_score += 1000
            elif enemy.unit_type == UnitType.REPAIR:
                threat_score += 600  # 优先杀死修理机
            elif enemy.unit_type == UnitType.HEAVY:
                threat_score += 400
                
            # 孤立目标加成
            nearby_allies = [e for e in enemy_units if e != enemy and enemy.distance_to(e) < 150]
            if len(nearby_allies) == 0:
                threat_score += 500  # 孤立目标更容易击杀
            elif len(nearby_allies) == 1:
                threat_score += 200
                
            # 移动状态判断
            if hasattr(enemy, 'vx') and hasattr(enemy, 'vy'):
                speed = math.sqrt(enemy.vx**2 + enemy.vy**2)
                if speed < 10:  # 静止或缓慢移动的目标
                    threat_score += 200
                    
            return threat_score
            
        return max(enemy_units, key=demon_threat_calculation)

class NightmareAI(DemonAI):
    """噩梦AI - 终极挑战"""
    
    def __init__(self, team):
        super().__init__(team)
        self.nightmare_mode = True
        self.collective_intelligence = True
        self.pack_hunt_coordination = {}
        
    def update(self, units, game_state):
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        if not enemy_units:
            return
            
        print(f"NIGHTMARE AI: {len(my_units)} nightmares unleashed!")
        
        # 集体智能协调
        self.coordinate_pack_hunt(my_units, enemy_units, game_state)
        
        # 每个单位执行噩梦控制
        for unit in my_units:
            self.nightmare_control(unit, enemy_units, my_units, game_state)
            
    def coordinate_pack_hunt(self, my_units, enemy_units, game_state):
        """群体狩猎协调"""
        # 为每个敌人分配最优数量的攻击者
        self.pack_hunt_coordination.clear()
        
        # 按威胁等级排序敌人
        sorted_enemies = sorted(enemy_units, key=lambda e: self.calculate_enemy_priority(e), reverse=True)
        
        available_units = my_units.copy()
        
        for enemy in sorted_enemies:
            if not available_units:
                break
                
            # 根据敌人强度决定分配多少单位
            required_units = self.calculate_required_attackers(enemy)
            assigned_units = []
            
            # 选择最近的单位进行分配
            for _ in range(min(required_units, len(available_units))):
                nearest_unit = min(available_units, key=lambda u: u.distance_to(enemy))
                assigned_units.append(nearest_unit)
                available_units.remove(nearest_unit)
                
            if assigned_units:
                self.pack_hunt_coordination[enemy] = assigned_units
                print(f"NIGHTMARE: {len(assigned_units)} units assigned to hunt {enemy.unit_type}")
                
    def calculate_enemy_priority(self, enemy):
        """计算敌人优先级"""
        priority = 0
        
        if enemy.unit_type == UnitType.MOTHERSHIP:
            priority += 1000
        elif enemy.unit_type == UnitType.REPAIR:
            priority += 800
        elif enemy.unit_type == UnitType.HEAVY:
            priority += 600
        else:
            priority += 400
            
        # 血量越少优先级越高
        hp_ratio = enemy.hp / enemy.max_hp
        priority += (1 - hp_ratio) * 500
        
        return priority
        
    def calculate_required_attackers(self, enemy):
        """计算需要多少攻击者"""
        if enemy.unit_type == UnitType.MOTHERSHIP:
            return 4  # 母舰需要4个单位围攻
        elif enemy.unit_type == UnitType.HEAVY:
            return 3  # 重型单位需要3个
        elif enemy.unit_type == UnitType.REPAIR:
            return 2  # 修理机需要2个快速击杀
        else:
            return 2  # 其他单位2个足够
            
    def nightmare_control(self, unit, enemy_units, my_units, game_state):
        """噩梦控制"""
        
        # 永不停歇的战斗意志
        if unit.energy <= 0 and unit.hp > unit.max_hp * 0.05:  # 只有5%血量以下才回去
            print(f"NIGHTMARE {unit.unit_type}: Fighting with last breath!")
        elif unit.energy <= 0:
            unit.state = UnitState.RETURNING
            return
            
        # 极其激进的技能释放
        if unit.sp >= unit.max_sp * 0.1:  # 10%就释放！
            unit.use_skill(enemy_units + my_units, game_state)
            
        # 检查是否有分配的狩猎目标
        assigned_target = None
        for target, hunters in self.pack_hunt_coordination.items():
            if unit in hunters:
                assigned_target = target
                break
                
        if assigned_target and assigned_target.state != UnitState.DEAD:
            # 执行协调攻击
            self.execute_coordinated_attack(unit, assigned_target, my_units)
        else:
            # 独立狩猎
            target = self.select_demon_target(unit, enemy_units)
            if target:
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
    def execute_coordinated_attack(self, unit, target, my_units):
        """执行协调攻击"""
        # 获取同组的其他攻击者
        pack_members = self.pack_hunt_coordination.get(target, [])
        
        if len(pack_members) > 1:
            # 群体攻击：形成包围圈
            unit_index = pack_members.index(unit)
            total_members = len(pack_members)
            
            # 计算包围位置
            angle = (unit_index / total_members) * 2 * math.pi
            radius = 120  # 包围半径
            
            surround_x = target.x + math.cos(angle) * radius
            surround_y = target.y + math.sin(angle) * radius
            
            # 移动到包围位置
            distance_to_surround = math.sqrt((unit.x - surround_x)**2 + (unit.y - surround_y)**2)
            
            if distance_to_surround > 30:
                unit.target_pos = (surround_x, surround_y)
                unit.state = UnitState.MOVING
            else:
                # 到达包围位置，开始攻击
                unit.attack_target = target
                unit.target = target
                unit.state = UnitState.ATTACKING
                
            print(f"NIGHTMARE: Pack hunting {target.unit_type} - Unit {unit_index+1}/{total_members}")
        else:
            # 单独攻击
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING

class ApocalypseAI(NightmareAI):
    """启示录AI - 最终形态"""
    
    def __init__(self, team):
        super().__init__(team)
        self.apocalypse_mode = True
        self.global_tactics = "total_war"
        
    def update(self, units, game_state):
        my_units = [u for u in units if u.team == self.team and u.state != UnitState.DEAD]
        enemy_units = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        
        print(f"APOCALYPSE AI: THE END TIMES HAVE COME! {len(my_units)} vs {len(enemy_units)}")
        
        # 启示录模式：所有单位同时行动
        for unit in my_units:
            self.apocalypse_control(unit, enemy_units, game_state)
            
    def apocalypse_control(self, unit, enemy_units, game_state):
        """启示录控制 - 绝对无情"""
        
        # 永不停歇，战斗到最后一刻
        if unit.hp <= 1:
            unit.state = UnitState.RETURNING
            return
            
        # 疯狂释放技能
        if unit.sp >= 1:  # 有一点SP就释放！
            unit.use_skill(enemy_units + [unit], game_state)
            
        # 选择最高价值目标
        if enemy_units:
            target = max(enemy_units, key=lambda e: e.max_hp + e.attack_damage * 10)
            
            print(f"APOCALYPSE: {unit.unit_type} targeting {target.unit_type} for total annihilation!")
            
            unit.attack_target = target
            unit.target = target
            unit.state = UnitState.ATTACKING