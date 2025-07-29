import pygame
import math
from config import COLOR_WHITE, COLOR_YELLOW, COLOR_ENEMY, COLOR_BLUE, COLOR_PURPLE, COLOR_CYAN

class Effect:
    def __init__(self, x, y, duration):
        self.x = x
        self.y = y
        self.duration = duration
        self.time = 0
        
    def update(self, dt):
        self.time += dt
        return self.time < self.duration
        
    def draw(self, screen, camera):
        pass

class ProjectileEffect(Effect):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, 0.2)
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, screen, camera):
        alpha = 1 - (self.time / self.duration)
        color = (255, int(255 * alpha), 0)
        
        sx1, sy1 = camera.world_to_screen(self.x, self.y)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        
        pygame.draw.line(screen, color, (sx1, sy1), (sx2, sy2), 2)

# 新增真正的投射物类
class Projectile:
    def __init__(self, x, y, target_x, target_y, damage, speed, target_unit=None):
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.damage = damage
        self.speed = speed
        self.target_unit = target_unit
        self.alive = True
        
    def update(self, dt, units, game_state):
        # 移动向目标
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 5:  # 到达目标
            # 造成伤害
            if self.target_unit and self.target_unit.state.value != "dead":
                self.target_unit.take_damage(self.damage)
            self.alive = False
            return False
            
        # 移动
        self.x += (dx / distance) * self.speed * dt
        self.y += (dy / distance) * self.speed * dt
        return True
        
    def draw(self, screen, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        pygame.draw.circle(screen, (255, 200, 0), (sx, sy), 3)

# 炮击投射物
class ArtilleryProjectile(Projectile):
    def __init__(self, x, y, target_x, target_y, damage, splash_radius, speed):
        super().__init__(x, y, target_x, target_y, damage, speed)
        self.splash_radius = splash_radius
        
    def update(self, dt, units, game_state):
        # 移动向目标
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 5:  # 到达目标
            # 范围伤害
            from units import UnitState
            for unit in units:
                if unit.state != UnitState.DEAD:
                    dist = math.sqrt((unit.x - self.x)**2 + (unit.y - self.y)**2)
                    if dist <= self.splash_radius:
                        damage_ratio = 1 - (dist / self.splash_radius) * 0.5
                        unit.take_damage(int(self.damage * damage_ratio))
            
            game_state.add_effect(ArtilleryEffect(self.x, self.y, self.splash_radius))
            self.alive = False
            return False
            
        # 移动
        self.x += (dx / distance) * self.speed * dt
        self.y += (dy / distance) * self.speed * dt
        return True

# 导弹投射物（会追踪）
class MissileProjectile(Projectile):
    def __init__(self, x, y, target_unit, damage, speed):
        super().__init__(x, y, target_unit.x, target_unit.y, damage, speed, target_unit)
        
    def update(self, dt, units, game_state):
        # 更新目标位置
        if self.target_unit and self.target_unit.state.value != "dead":
            self.target_x = self.target_unit.x
            self.target_y = self.target_unit.y
        
        return super().update(dt, units, game_state)
        
    def draw(self, screen, camera):
        sx, sy = camera.world_to_screen(self.x, self.y)
        # 绘制导弹
        pygame.draw.circle(screen, (255, 100, 100), (sx, sy), 4)
        # 绘制尾焰
        trail_x = self.x - (self.target_x - self.x) * 0.1
        trail_y = self.y - (self.target_y - self.y) * 0.1
        tsx, tsy = camera.world_to_screen(trail_x, trail_y)
        pygame.draw.line(screen, (255, 200, 100), (tsx, tsy), (sx, sy), 2)

# 光束效果
class BeamEffect(Effect):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, 0.3)
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        alpha = 1 - progress
        
        sx1, sy1 = camera.world_to_screen(self.x, self.y)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        
        # 绘制光束
        width = int(8 * (1 - progress) * camera.zoom)
        if width > 0:
            pygame.draw.line(screen, COLOR_CYAN, (sx1, sy1), (sx2, sy2), width)

class MeleeEffect(Effect):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, 0.3)
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        color = (255, 255, 255)
        
        sx1, sy1 = camera.world_to_screen(self.x, self.y)
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        
        # 绘制冲击波
        radius = int(30 * progress * camera.zoom)
        if radius > 0:
            pygame.draw.circle(screen, color, (sx2, sy2), radius, 2)

class ArtilleryEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 0.5)
        self.explosion_radius = radius
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 爆炸效果
        color = (255, int(255 * (1 - progress)), 0)
        radius = int(self.explosion_radius * progress * camera.zoom)
        if radius > 0:
            pygame.draw.circle(screen, color, (sx, sy), radius, 3)

class MissileEffect(Effect):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, 0.4)
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        
        # 导弹轨迹
        current_x = self.x + (self.x2 - self.x) * progress
        current_y = self.y + (self.y2 - self.y) * progress
        
        sx, sy = camera.world_to_screen(current_x, current_y)
        
        # 绘制导弹
        pygame.draw.circle(screen, (255, 255, 255), (sx, sy), int(3 * camera.zoom))
        
        # 到达目标时爆炸
        if progress > 0.8:
            explosion_radius = int(20 * camera.zoom)
            pygame.draw.circle(screen, COLOR_ENEMY, (sx, sy), explosion_radius, 2)

class SkillEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 1.0)
        self.radius = radius
        
    def draw(self, screen, camera):
        alpha = 1 - (self.time / self.duration)
        current_radius = self.radius * (self.time / self.duration)
        
        sx, sy = camera.world_to_screen(self.x, self.y)
        radius = int(current_radius * camera.zoom)
        
        if radius > 0:
            pygame.draw.circle(screen, COLOR_WHITE, (sx, sy), radius, 2)

class ExplosionEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 0.8)
        self.radius = radius
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 多层爆炸效果
        for i in range(3):
            alpha = 1 - (progress + i * 0.1)
            if alpha > 0:
                color = (255, int(200 * alpha), int(100 * alpha))
                radius = int((self.radius * (progress + i * 0.1)) * camera.zoom)
                if radius > 0:
                    pygame.draw.circle(screen, color, (sx, sy), radius, 2)

class HealEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 1.0)
        self.radius = radius
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 治疗光环
        color = (0, 255, int(255 * (1 - progress)))
        radius = int(self.radius * progress * camera.zoom)
        if radius > 0:
            pygame.draw.circle(screen, color, (sx, sy), radius, 2)

class BuffEffect(Effect):
    def __init__(self, x, y, radius, color):
        super().__init__(x, y, 0.5)
        self.radius = radius
        self.color = color
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 增益光环
        alpha = 1 - progress
        radius = int(self.radius * camera.zoom)
        if radius > 0:
            for i in range(3):
                pygame.draw.circle(screen, self.color, (sx, sy), 
                                 radius - i * 20, 2)

class ShieldEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 1.0)
        self.radius = radius
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 护盾展开效果
        radius = int(self.radius * progress * camera.zoom)
        if radius > 0:
            pygame.draw.circle(screen, COLOR_CYAN, (sx, sy), radius, 3)

class TeleportEffect(Effect):
    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1, y1, 0.5)
        self.x2 = x2
        self.y2 = y2
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        
        # 传送起点效果
        sx1, sy1 = camera.world_to_screen(self.x, self.y)
        radius1 = int(30 * (1 - progress) * camera.zoom)
        if radius1 > 0:
            pygame.draw.circle(screen, COLOR_PURPLE, (sx1, sy1), radius1, 2)
            
        # 传送终点效果
        sx2, sy2 = camera.world_to_screen(self.x2, self.y2)
        radius2 = int(30 * progress * camera.zoom)
        if radius2 > 0:
            pygame.draw.circle(screen, COLOR_PURPLE, (sx2, sy2), radius2, 2)

class DisableEffect(Effect):
    def __init__(self, x, y, radius):
        super().__init__(x, y, 0.8)
        self.radius = radius
        
    def draw(self, screen, camera):
        progress = self.time / self.duration
        sx, sy = camera.world_to_screen(self.x, self.y)
        
        # 禁用效果
        radius = int(self.radius * camera.zoom)
        if radius > 0:
            color = (200, 0, 200)
            pygame.draw.circle(screen, color, (sx, sy), radius, 2)

class GlobalHealEffect(Effect):
    def __init__(self):
        super().__init__(0, 0, 2.0)
        
    def draw(self, screen, camera):
        # 全屏治疗效果
        progress = self.time / self.duration
        alpha = int(50 * (1 - abs(progress - 0.5) * 2))
        
        # 创建绿色覆盖层
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(alpha)
        overlay.fill((0, 255, 0))
        screen.blit(overlay, (0, 0))

# 为了向后兼容，保留旧的 AttackEffect
AttackEffect = ProjectileEffect