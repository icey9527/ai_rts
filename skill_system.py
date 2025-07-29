import pygame
import math
import random
from config import *
from effects import *

class SkillSystem:
    @staticmethod
    def execute_skill(unit, skill_data, units, game_state):
        """执行技能"""
        skill_type = SkillType(skill_data.get("type", "damage_aoe"))
        
        if skill_type == SkillType.DAMAGE_AOE:
            SkillSystem.damage_aoe(unit, skill_data, units, game_state)
        elif skill_type == SkillType.HEAL_AOE:
            SkillSystem.heal_aoe(unit, skill_data, units, game_state)
        elif skill_type == SkillType.BUFF_SPEED:
            SkillSystem.buff_speed(unit, skill_data, units, game_state)
        elif skill_type == SkillType.BUFF_ATTACK:
            SkillSystem.buff_attack(unit, skill_data, units, game_state)
        elif skill_type == SkillType.SHIELD:
            SkillSystem.shield(unit, skill_data, units, game_state)
        elif skill_type == SkillType.TELEPORT:
            SkillSystem.teleport(unit, skill_data, units, game_state)
        elif skill_type == SkillType.DISABLE:
            SkillSystem.disable(unit, skill_data, units, game_state)
        elif skill_type == SkillType.REPAIR_ALL:
            SkillSystem.repair_all(unit, skill_data, units, game_state)
            
    @staticmethod
    def damage_aoe(unit, skill_data, units, game_state):
        """范围伤害"""
        radius = skill_data.get("radius", 200)
        damage = skill_data.get("damage", 100)
        
        for target in units:
            if target.team != unit.team and unit.distance_to(target) <= radius:
                target.take_damage(damage)
                
        game_state.add_effect(ExplosionEffect(unit.x, unit.y, radius))
        
    @staticmethod
    def heal_aoe(unit, skill_data, units, game_state):
        """范围治疗"""
        radius = skill_data.get("radius", 200)
        heal = skill_data.get("heal", 50)
        
        for target in units:
            if target.team == unit.team and unit.distance_to(target) <= radius:
                target.hp = min(target.hp + heal, target.max_hp)
                
        game_state.add_effect(HealEffect(unit.x, unit.y, radius))
        
    @staticmethod
    def buff_speed(unit, skill_data, units, game_state):
        """速度加成"""
        radius = skill_data.get("radius", 200)
        speed_multiplier = skill_data.get("speed_multiplier", 1.5)
        duration = skill_data.get("duration", 10.0)
        
        for target in units:
            if target.team == unit.team and unit.distance_to(target) <= radius:
                target.apply_buff("speed", speed_multiplier, duration)
                
        game_state.add_effect(BuffEffect(unit.x, unit.y, radius, COLOR_YELLOW))
        
    @staticmethod
    def buff_attack(unit, skill_data, units, game_state):
        """攻击加成"""
        radius = skill_data.get("radius", 200)
        attack_multiplier = skill_data.get("attack_multiplier", 1.5)
        duration = skill_data.get("duration", 10.0)
        
        for target in units:
            if target.team == unit.team and unit.distance_to(target) <= radius:
                target.apply_buff("attack", attack_multiplier, duration)
                
        game_state.add_effect(BuffEffect(unit.x, unit.y, radius, COLOR_ENEMY))
        
    @staticmethod
    def shield(unit, skill_data, units, game_state):
        """护盾"""
        radius = skill_data.get("radius", 200)
        shield_amount = skill_data.get("shield_amount", 50)
        duration = skill_data.get("duration", 15.0)
        
        for target in units:
            if target.team == unit.team and unit.distance_to(target) <= radius:
                target.apply_shield(shield_amount, duration)
                
        game_state.add_effect(ShieldEffect(unit.x, unit.y, radius))
        
    @staticmethod
    def teleport(unit, skill_data, units, game_state):
        """传送"""
        radius = skill_data.get("radius", 300)
        # 随机传送到附近位置
        angle = random.random() * 2 * math.pi
        distance = random.uniform(100, radius)
        
        new_x = unit.x + math.cos(angle) * distance
        new_y = unit.y + math.sin(angle) * distance
        
        # 检查位置是否有效
        if hasattr(game_state, 'terrain_manager'):
            new_x, new_y = game_state.find_clear_position_near(new_x, new_y, unit.radius)
            
        game_state.add_effect(TeleportEffect(unit.x, unit.y, new_x, new_y))
        unit.x = new_x
        unit.y = new_y
        
    @staticmethod
    def disable(unit, skill_data, units, game_state):
        """禁用敌人"""
        radius = skill_data.get("radius", 200)
        duration = skill_data.get("duration", 5.0)
        
        for target in units:
            if target.team != unit.team and unit.distance_to(target) <= radius:
                target.apply_debuff("disable", duration)
                
        game_state.add_effect(DisableEffect(unit.x, unit.y, radius))
        
    @staticmethod
    def repair_all(unit, skill_data, units, game_state):
        """全体修理"""
        heal = skill_data.get("heal", 30)
        
        for target in units:
            if target.team == unit.team:
                target.hp = min(target.hp + heal, target.max_hp)
                
        game_state.add_effect(GlobalHealEffect())