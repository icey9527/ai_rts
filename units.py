import pygame
import math
import random
from enum import Enum
from config import *

class UnitState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    ATTACKING = "attacking"
    REPAIRING = "repairing"
    RETURNING = "returning"
    SUPPLYING = "supplying"
    FOLLOWING = "following"
    DISABLED = "disabled"
    CIRCLE_STRAFING = "circle_strafing"  # 围绕攻击
    DEAD = "dead"

class GameObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = 20
        self.selected = False
        self.sprite_name = None
        
    def distance_to(self, other):
        if hasattr(other, 'x') and hasattr(other, 'y'):
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
        return float('inf')
    
    def move_towards(self, target_x, target_y, speed, terrain_manager=None):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            # 检查路径是否被阻挡
            if terrain_manager and terrain_manager.is_position_blocked(target_x, target_y, self.radius):
                # 如果目标位置被阻挡，尝试绕行
                detour_points = terrain_manager.find_detour(self.x, self.y, target_x, target_y, self.radius)
                if detour_points:
                    target_x, target_y = detour_points[0]
                    dx = target_x - self.x
                    dy = target_y - self.y
                    distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                self.vx = (dx / distance) * speed
                self.vy = (dy / distance) * speed
                self.x += self.vx
                self.y += self.vy
                return distance > speed
        return False
        
    def draw(self, screen, camera, sprite_manager):
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # 尝试绘制精灵
        sprite = sprite_manager.get_sprite(self.sprite_name)
        if sprite:
            size = int(self.radius * 2 * camera.zoom)
            sprite = pygame.transform.scale(sprite, (size, size))
            screen.blit(sprite, (screen_x - size//2, screen_y - size//2))
        else:
            # 默认绘制
            radius = int(self.radius * camera.zoom)
            color = self.get_default_color() if hasattr(self, 'get_default_color') else COLOR_WHITE
            pygame.draw.circle(screen, color, (screen_x, screen_y), radius, 2)

class Unit(GameObject):
    def __init__(self, x, y, team, unit_data):
        super().__init__(x, y)
        self.team = team
        self.unit_type = UnitType(unit_data["type"])
        
        # 单位信息
        self.name = unit_data.get("name", "未知单位")
        self.description = unit_data.get("description", "暂无描述")
        
        self.max_hp = unit_data["max_hp"]
        self.hp = self.max_hp
        self.max_energy = unit_data.get("max_energy", 100)
        self.energy = self.max_energy
        self.base_speed = unit_data["speed"]
        self.speed = self.base_speed
        self.base_attack_damage = unit_data.get("attack_damage", 0)
        self.attack_damage = self.base_attack_damage
        self.attack_range = unit_data.get("attack_range", 0)
        self.attack_cooldown = unit_data.get("attack_cooldown", 1.0)
        self.radius = unit_data.get("radius", 20)
        self.last_attack_time = 0
        
        # 攻击类型
        self.attack_type = AttackType(unit_data.get("attack_type", "ranged"))
        self.projectile_count = unit_data.get("projectile_count", 1)
        self.splash_radius = unit_data.get("splash_radius", 0)
        self.projectile_speed = unit_data.get("projectile_speed", 400)  # 弹道速度
        
        # SP系统（母舰没有）
        if self.unit_type != UnitType.MOTHERSHIP:
            self.sp = 0
            self.max_sp = 100
            self.skill_data = unit_data.get("skill", {})
        else:
            self.sp = 0
            self.max_sp = 0
            self.skill_data = {}
            
        self.state = UnitState.IDLE
        self.target = None
        self.target_pos = None
        self.follow_target = None
        self.attack_target = None
        self.repair_target = None
        
        # 围绕攻击相关
        self.circle_angle = random.random() * 2 * math.pi  # 随机初始角度
        self.circle_direction = random.choice([-1, 1])  # 随机方向
        
        # 修理相关
        self.repair_range = unit_data.get("repair_range", 100)
        self.repair_rate = unit_data.get("repair_rate", 10)
        
        # Buff/Debuff系统
        self.buffs = {}
        self.shield = 0
        self.shield_time = 0
        
        # 补给状态
        self.is_supplying = False
        self.supply_target = None
        
        # 精灵
        self.sprite_name = unit_data.get("sprite", None)
        
    def get_default_color(self):
        if self.unit_type == UnitType.HEAVY:
            return (150, 150, 255) if self.team == 0 else (255, 150, 150)
        elif self.unit_type == UnitType.SCOUT:
            return (255, 255, 150) if self.team == 0 else (255, 200, 150)
        elif self.unit_type == UnitType.BOMBER:
            return (255, 150, 255) if self.team == 0 else (255, 100, 255)
        else:
            return COLOR_PLAYER if self.team == 0 else COLOR_ENEMY
        
    def apply_buff(self, buff_type, multiplier, duration):
        """应用增益效果"""
        self.buffs[buff_type] = (multiplier, duration)
        self.update_stats()
        
    def apply_shield(self, amount, duration):
        """应用护盾"""
        self.shield = amount
        self.shield_time = duration
        
    def apply_debuff(self, debuff_type, duration):
        """应用负面效果"""
        if debuff_type == "disable":
            self.state = UnitState.DISABLED
            self.buffs["disable"] = (1.0, duration)
            
    def update_stats(self):
        """更新单位属性"""
        # 重置属性
        self.speed = self.base_speed
        self.attack_damage = self.base_attack_damage
        
        # 应用buff效果
        for buff_type, (multiplier, _) in self.buffs.items():
            if buff_type == "speed":
                self.speed *= multiplier
            elif buff_type == "attack":
                self.attack_damage = int(self.attack_damage * multiplier)
                
    def find_nearest_enemy(self, units, max_range=None):
        """查找最近的敌方单位"""
        enemies = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
        if not enemies:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for enemy in enemies:
            distance = self.distance_to(enemy)
            if max_range and distance > max_range:
                continue
            if distance < min_distance:
                min_distance = distance
                nearest = enemy
                
        return nearest
        
    def update(self, dt, units, game_state):
        if self.state == UnitState.DEAD:
            return
            
        # 首先获取地形管理器
        terrain_manager = getattr(game_state, 'terrain_manager', None)
            
        # 更新buff/debuff
        expired_buffs = []
        for buff_type, (multiplier, remaining_time) in self.buffs.items():
            remaining_time -= dt
            if remaining_time <= 0:
                expired_buffs.append(buff_type)
            else:
                self.buffs[buff_type] = (multiplier, remaining_time)
                
        for buff_type in expired_buffs:
            del self.buffs[buff_type]
            if buff_type == "disable":
                self.state = UnitState.IDLE
                
        # 更新属性
        self.update_stats()
        
        # 更新护盾
        if self.shield_time > 0:
            self.shield_time -= dt
            if self.shield_time <= 0:
                self.shield = 0
                
        # 如果被禁用，不执行其他逻辑
        if self.state == UnitState.DISABLED:
            return
            
        # 我方单位非常有限的自动行为
        if self.team == 0:
            # 自动释放必杀技（满SP时）
            if (self.sp >= self.max_sp and 
                self.skill_data and 
                self.unit_type != UnitType.MOTHERSHIP):
                print(f"Player {self.unit_type} auto-using skill!")
                self.use_skill(units, game_state)
                
            # 自动补给（能量很低且空闲时）
            if (self.energy < 20 and 
                self.state == UnitState.IDLE and
                self.unit_type != UnitType.MOTHERSHIP):
                mothership = self.find_mothership(units)
                if mothership:
                    print(f"Player {self.unit_type} auto-returning for supply")
                    self.state = UnitState.RETURNING
                    
            # 极小范围的自动寻敌（只有在完全空闲且敌人很近时）
            if (self.unit_type in [UnitType.FIGHTER, UnitType.SCOUT, UnitType.HEAVY, UnitType.BOMBER, UnitType.INTERCEPTOR] and
                self.state == UnitState.IDLE and
                not self.attack_target and
                self.energy > 50):  # 需要充足能量
                
                # 很小的寻敌范围，只有敌人很近才自动攻击
                enemy = self.find_nearest_enemy(units, 150)  # 大幅缩小范围
                if enemy:
                    self.attack_target = enemy
                    self.state = UnitState.ATTACKING
                    print(f"Player {self.unit_type} auto-engaging nearby enemy")
                    
            # 修理机自动修理（非常被动）
            if (self.unit_type == UnitType.REPAIR and
                self.state == UnitState.IDLE and
                not self.repair_target and
                self.energy > 30):
                
                # 只修理非常近的严重受伤友军
                damaged_allies = [u for u in units 
                                if (u.team == self.team and 
                                    u != self and
                                    u.hp < u.max_hp * 0.5 and  # 只修理血量低于50%的
                                    self.distance_to(u) < 100)]  # 很近才修理
                if damaged_allies:
                    target = min(damaged_allies, key=lambda u: u.hp / u.max_hp)
                    self.repair_target = target
                    self.target = target
                    self.state = UnitState.REPAIRING
            
        # 更新状态
        if self.state == UnitState.MOVING and self.target_pos:
            if not self.move_towards(self.target_pos[0], self.target_pos[1], self.speed * dt, terrain_manager):
                self.state = UnitState.IDLE
                self.target_pos = None
                
        elif self.state == UnitState.ATTACKING:
            # 追击逻辑
            if self.attack_target and self.attack_target.state != UnitState.DEAD:
                distance_to_target = self.distance_to(self.attack_target)
                
                # 如果是战斗机类型，使用围绕攻击
                if self.unit_type in [UnitType.FIGHTER, UnitType.SCOUT, UnitType.INTERCEPTOR]:
                    if distance_to_target <= self.attack_range + CIRCLE_STRAFE_RADIUS:
                        self.state = UnitState.CIRCLE_STRAFING
                    else:
                        # 追击
                        self.move_towards(self.attack_target.x, self.attack_target.y, self.speed * dt, terrain_manager)
                        if self.team == 1:  # AI单位打印追击信息
                            print(f"AI {self.unit_type} chasing {self.attack_target.unit_type}, distance: {distance_to_target:.1f}")
                else:
                    # 其他单位正常攻击
                    if distance_to_target <= self.attack_range:
                        self.target = self.attack_target
                        self.perform_attack(game_state)
                    else:
                        # 追击
                        self.move_towards(self.attack_target.x, self.attack_target.y, self.speed * dt, terrain_manager)
                        if self.team == 1:  # AI单位打印追击信息
                            print(f"AI {self.unit_type} pursuing {self.attack_target.unit_type}, distance: {distance_to_target:.1f}")
            else:
                # 目标消失，AI单位立即寻找新目标，玩家单位停止
                if self.team == 1:  # 如果是AI单位
                    all_enemies = [u for u in units if u.team != self.team and u.state != UnitState.DEAD]
                    if all_enemies:
                        new_target = min(all_enemies, key=lambda e: self.distance_to(e))
                        self.attack_target = new_target
                        self.target = new_target
                        print(f"AI {self.unit_type} acquired new target: {new_target.unit_type}")
                    else:
                        self.state = UnitState.IDLE
                        self.attack_target = None
                        self.target = None
                else:
                    # 玩家单位目标消失后进入空闲状态，需要玩家手动指挥
                    self.state = UnitState.IDLE
                    self.attack_target = None
                    self.target = None
                    
        elif self.state == UnitState.CIRCLE_STRAFING:
            # 围绕攻击
            if self.attack_target and self.attack_target.state != UnitState.DEAD:
                distance_to_target = self.distance_to(self.attack_target)
                
                if distance_to_target > self.attack_range + CIRCLE_STRAFE_RADIUS * 2:
                    self.state = UnitState.ATTACKING
                else:
                    self.circle_angle += CIRCLE_STRAFE_SPEED * dt * self.circle_direction
                    circle_x = self.attack_target.x + math.cos(self.circle_angle) * CIRCLE_STRAFE_RADIUS
                    circle_y = self.attack_target.y + math.sin(self.circle_angle) * CIRCLE_STRAFE_RADIUS
                    self.move_towards(circle_x, circle_y, self.speed * dt, terrain_manager)
                    
                    if distance_to_target <= self.attack_range:
                        self.target = self.attack_target
                        self.perform_attack(game_state)
            else:
                self.state = UnitState.IDLE
                self.attack_target = None
                
        elif self.state == UnitState.REPAIRING:
            if self.repair_target and self.repair_target.state != UnitState.DEAD and self.repair_target.hp < self.repair_target.max_hp:
                distance_to_target = self.distance_to(self.repair_target)
                
                if distance_to_target <= self.repair_range:
                    self.target = self.repair_target
                    self.perform_repair(dt)
                else:
                    self.move_towards(self.repair_target.x, self.repair_target.y, self.speed * dt, terrain_manager)
            else:
                self.state = UnitState.IDLE
                self.repair_target = None
                self.target = None
                
        elif self.state == UnitState.FOLLOWING and self.follow_target:
            if self.follow_target.state == UnitState.DEAD:
                self.state = UnitState.IDLE
                self.follow_target = None
            else:
                distance = self.distance_to(self.follow_target)
                if distance > 80:
                    self.move_towards(self.follow_target.x, self.follow_target.y, self.speed * dt, terrain_manager)
                
                if (self.follow_target.state == UnitState.ATTACKING and 
                    self.follow_target.attack_target and
                    self.attack_damage > 0 and 
                    self.unit_type != UnitType.REPAIR):
                    if self.distance_to(self.follow_target.attack_target) <= self.attack_range:
                        self.attack_target = self.follow_target.attack_target
                        self.target = self.attack_target
                        self.perform_attack(game_state)
                
        elif self.state == UnitState.RETURNING:
            mothership = self.find_mothership(units)
            if mothership and self.distance_to(mothership) < MOTHERSHIP_SUPPLY_RANGE:
                if mothership.unit_type == UnitType.MOTHERSHIP:
                    self.state = UnitState.SUPPLYING
                    mothership.supply_target = self
            elif mothership:
                self.move_towards(mothership.x, mothership.y, self.speed * dt, terrain_manager)
                
        elif self.state == UnitState.SUPPLYING:
            mothership = self.find_mothership(units)
            if mothership and self.distance_to(mothership) < MOTHERSHIP_SUPPLY_RANGE:
                supply_amount = SUPPLY_RATE * dt
                self.energy = min(self.energy + supply_amount, self.max_energy)
                
                from config import SUPPLY_HP_RATE
                heal_amount = SUPPLY_HP_RATE * dt
                self.hp = min(self.hp + heal_amount, self.max_hp)
                
                if self.energy >= self.max_energy and self.hp >= self.max_hp:
                    self.state = UnitState.IDLE
                    if mothership.supply_target == self:
                        mothership.supply_target = None
            else:
                self.state = UnitState.IDLE
                
        # 母舰处理补给请求
        if self.unit_type == UnitType.MOTHERSHIP and self.supply_target:
            if (self.supply_target.state != UnitState.SUPPLYING or 
                self.distance_to(self.supply_target) > MOTHERSHIP_SUPPLY_RANGE):
                self.supply_target = None
                
    def perform_attack(self, game_state):
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_attack_time >= self.attack_cooldown:
            energy_cost = ENERGY_ATTACK_COST if self.unit_type != UnitType.MOTHERSHIP else 0
            if self.energy >= energy_cost:
                if self.attack_type == AttackType.MELEE:
                    self.perform_melee_attack(game_state)
                elif self.attack_type == AttackType.ARTILLERY:
                    self.perform_artillery_attack(game_state)
                elif self.attack_type == AttackType.MISSILE:
                    self.perform_missile_attack(game_state)
                elif self.attack_type == AttackType.BEAM:
                    self.perform_beam_attack(game_state)
                else:
                    self.perform_ranged_attack(game_state)
                    
                self.energy -= energy_cost
                
                if self.unit_type != UnitType.MOTHERSHIP:
                    self.sp = min(self.sp + SP_GAIN_PER_ATTACK, self.max_sp)
                    
                self.last_attack_time = current_time
                
    def perform_repair(self, dt):
        """执行修理"""
        if self.target and self.energy >= ENERGY_REPAIR_COST:
            repair_amount = self.repair_rate * dt
            self.target.hp = min(self.target.hp + repair_amount, self.target.max_hp)
            self.energy -= ENERGY_REPAIR_COST * dt
                
    def perform_melee_attack(self, game_state):
        self.target.take_damage(self.attack_damage)
        from effects import MeleeEffect
        game_state.add_effect(MeleeEffect(self.x, self.y, self.target.x, self.target.y))
        
    def perform_ranged_attack(self, game_state):
        for i in range(self.projectile_count):
            if self.projectile_count > 1:
                angle_offset = (i - self.projectile_count//2) * 0.2
                target_x = self.target.x + math.cos(angle_offset) * 20
                target_y = self.target.y + math.sin(angle_offset) * 20
            else:
                target_x, target_y = self.target.x, self.target.y
                
            # 创建投射物而不是特效
            from effects import Projectile
            projectile = Projectile(self.x, self.y, target_x, target_y,
                                  self.attack_damage // self.projectile_count,
                                  self.projectile_speed, self.target)
            game_state.add_projectile(projectile)
            
            # 添加发射特效
            from effects import ProjectileEffect
            game_state.add_effect(ProjectileEffect(self.x, self.y, target_x, target_y))
            
    def perform_artillery_attack(self, game_state):
        from effects import ArtilleryProjectile
        # 炮击有飞行时间，可以躲避
        projectile = ArtilleryProjectile(self.x, self.y, self.target.x, self.target.y,
                                       self.attack_damage, self.splash_radius, 200)
        game_state.add_projectile(projectile)
        
    def perform_missile_attack(self, game_state):
        from effects import MissileProjectile
        # 导弹会追踪目标
        projectile = MissileProjectile(self.x, self.y, self.target, self.attack_damage, 300)
        game_state.add_projectile(projectile)
        
    def perform_beam_attack(self, game_state):
        # 光束瞬间命中
        self.target.take_damage(self.attack_damage)
        from effects import BeamEffect
        game_state.add_effect(BeamEffect(self.x, self.y, self.target.x, self.target.y))
    
    def take_damage(self, damage):
        # 护盾优先承受伤害
        if self.shield > 0:
            shield_damage = min(damage, self.shield)
            self.shield -= shield_damage
            damage -= shield_damage
            
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.state = UnitState.DEAD
            
    def find_mothership(self, units):
        for unit in units:
            if unit.team == self.team and unit.unit_type == UnitType.MOTHERSHIP:
                return unit
        return None
    
    def use_skill(self, units, game_state):
        if self.unit_type == UnitType.MOTHERSHIP or not self.skill_data:
            return
            
        if self.sp >= self.max_sp:
            from skill_system import SkillSystem
            SkillSystem.execute_skill(self, self.skill_data, units, game_state)
            self.sp = 0
            
    def draw(self, screen, camera, sprite_manager):
        super().draw(screen, camera, sprite_manager)
        
        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        
        # 绘制护盾
        if self.shield > 0:
            shield_radius = int((self.radius + 8) * camera.zoom)
            pygame.draw.circle(screen, COLOR_CYAN, (screen_x, screen_y), shield_radius, 2)
        
        # 绘制禁用效果
        if self.state == UnitState.DISABLED:
            disable_radius = int((self.radius + 12) * camera.zoom)
            pygame.draw.circle(screen, COLOR_PURPLE, (screen_x, screen_y), disable_radius, 2)
        
        # 绘制血条
        bar_width = int(40 * camera.zoom)
        bar_height = int(4 * camera.zoom)
        bar_offset = int((self.radius + 15) * camera.zoom)
        
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, COLOR_ENEMY, 
                       (screen_x - bar_width//2, screen_y - bar_offset, 
                        bar_width, bar_height))
        pygame.draw.rect(screen, COLOR_PLAYER, 
                       (screen_x - bar_width//2, screen_y - bar_offset, 
                        int(bar_width * hp_ratio), bar_height))
                        
        # 绘制能量条
        if self.max_energy > 0:
            energy_ratio = self.energy / self.max_energy
            pygame.draw.rect(screen, COLOR_GRAY, 
                           (screen_x - bar_width//2, screen_y - bar_offset - bar_height - 2, 
                            bar_width, bar_height))
            pygame.draw.rect(screen, COLOR_BLUE, 
                           (screen_x - bar_width//2, screen_y - bar_offset - bar_height - 2, 
                            int(bar_width * energy_ratio), bar_height))
                            
        # 绘制SP条
        if self.unit_type != UnitType.MOTHERSHIP and self.max_sp > 0:
            sp_ratio = self.sp / self.max_sp
            pygame.draw.rect(screen, COLOR_GRAY, 
                           (screen_x - bar_width//2, screen_y - bar_offset - (bar_height + 2) * 2, 
                            bar_width, bar_height))
            pygame.draw.rect(screen, COLOR_YELLOW, 
                           (screen_x - bar_width//2, screen_y - bar_offset - (bar_height + 2) * 2, 
                            int(bar_width * sp_ratio), bar_height))
                            
        # 绘制选中框
        if self.selected:
            radius = int((self.radius + 5) * camera.zoom)
            color = COLOR_WHITE if self.team == 0 else COLOR_YELLOW
            pygame.draw.circle(screen, color, (screen_x, screen_y), radius, 2)
                             
        # 绘制状态指示
        if self.state == UnitState.SUPPLYING:
            pygame.draw.circle(screen, COLOR_BLUE, (screen_x, screen_y - int(35 * camera.zoom)), 
                             int(5 * camera.zoom))
        elif self.state == UnitState.FOLLOWING:
            pygame.draw.circle(screen, COLOR_YELLOW, (screen_x, screen_y - int(35 * camera.zoom)), 
                             int(5 * camera.zoom))
        elif self.state in [UnitState.ATTACKING, UnitState.CIRCLE_STRAFING] and self.attack_target:
            # 绘制追击指示线
            if camera.zoom > 0.5:
                target_x, target_y = camera.world_to_screen(self.attack_target.x, self.attack_target.y)
                pygame.draw.line(screen, COLOR_ENEMY, (screen_x, screen_y), (target_x, target_y), 1)
        elif self.state == UnitState.REPAIRING and self.repair_target:
            # 绘制修理指示线
            if camera.zoom > 0.5:
                target_x, target_y = camera.world_to_screen(self.repair_target.x, self.repair_target.y)
                pygame.draw.line(screen, (0, 255, 0), (screen_x, screen_y), (target_x, target_y), 1)

class RepairUnit(Unit):
    def __init__(self, x, y, team, unit_data):
        super().__init__(x, y, team, unit_data)