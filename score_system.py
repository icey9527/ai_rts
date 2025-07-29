import time
import json
import os
from config import *

class ScoreSystem:
    def __init__(self):
        self.level_start_time = 0
        self.level_end_time = 0
        self.initial_player_units = 0
        self.surviving_player_units = 0
        self.defeated_enemies = 0
        self.total_enemies = 0
        self.mothership_survived = False
        
    def start_level(self, player_units_count, enemy_units_count):
        """开始关卡计时"""
        self.level_start_time = time.time()
        self.initial_player_units = player_units_count
        self.total_enemies = enemy_units_count
        self.defeated_enemies = 0
        
    def end_level(self, game_state):
        """结束关卡，计算分数"""
        self.level_end_time = time.time()
        
        # 统计存活单位
        from units import UnitType, UnitState
        self.surviving_player_units = 0
        self.mothership_survived = False
        
        for unit in game_state.units:
            if unit.team == game_state.player_team and unit.state != UnitState.DEAD:
                self.surviving_player_units += 1
                if unit.unit_type == UnitType.MOTHERSHIP:
                    self.mothership_survived = True
                    
        # 计算击败的敌人数量
        self.defeated_enemies = self.total_enemies - len([u for u in game_state.units 
                                                         if u.team != game_state.player_team 
                                                         and u.state != UnitState.DEAD])
        
        return self.calculate_score()
        
    def calculate_score(self):
        """计算最终分数"""
        score = 0
        score_breakdown = {}
        
        # 基础胜利分数
        score += SCORE_BASE_VICTORY
        score_breakdown["胜利奖励"] = SCORE_BASE_VICTORY
        
        # 时间奖励
        elapsed_time = self.level_end_time - self.level_start_time
        if elapsed_time <= SCORE_TIME_TARGET:
            time_bonus = SCORE_TIME_BONUS_MAX
        else:
            time_bonus = max(0, SCORE_TIME_BONUS_MAX * (1 - (elapsed_time - SCORE_TIME_TARGET) / SCORE_TIME_TARGET))
        
        score += int(time_bonus)
        score_breakdown["时间奖励"] = int(time_bonus)
        score_breakdown["用时"] = f"{elapsed_time:.1f}秒"
        
        # 单位存活奖励
        survival_bonus = self.surviving_player_units * SCORE_UNIT_SURVIVAL
        score += survival_bonus
        score_breakdown["单位存活"] = f"{self.surviving_player_units}/{self.initial_player_units} (+{survival_bonus})"
        
        # 母舰存活奖励
        if self.mothership_survived:
            score += SCORE_MOTHERSHIP_SURVIVAL
            score_breakdown["母舰存活"] = SCORE_MOTHERSHIP_SURVIVAL
            
        # 敌人击败奖励
        enemy_bonus = self.defeated_enemies * SCORE_ENEMY_DEFEAT
        score += enemy_bonus
        score_breakdown["击败敌人"] = f"{self.defeated_enemies}/{self.total_enemies} (+{enemy_bonus})"
        
        # 完美胜利奖励
        if self.surviving_player_units == self.initial_player_units:
            score += SCORE_PERFECT_VICTORY
            score_breakdown["完美胜利"] = SCORE_PERFECT_VICTORY
            
        return score, score_breakdown
        
    def save_high_score(self, level_name, score):
        """保存最高分"""
        scores_file = "high_scores.json"
        scores = {}
        
        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r', encoding='utf-8') as f:
                    scores = json.load(f)
            except:
                scores = {}
                
        if level_name not in scores or score > scores[level_name]:
            scores[level_name] = score
            
            try:
                with open(scores_file, 'w', encoding='utf-8') as f:
                    json.dump(scores, f, ensure_ascii=False, indent=2)
                return True  # 新纪录
            except:
                pass
                
        return False  # 不是新纪录
        
    def get_high_score(self, level_name):
        """获取最高分"""
        scores_file = "high_scores.json"
        if os.path.exists(scores_file):
            try:
                with open(scores_file, 'r', encoding='utf-8') as f:
                    scores = json.load(f)
                    return scores.get(level_name, 0)
            except:
                pass
        return 0