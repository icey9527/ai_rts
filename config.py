# 游戏配置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# 地图设置
MAP_WIDTH = 2400
MAP_HEIGHT = 2400

# 边缘滚动设置
EDGE_SCROLL_MARGIN = 50  # 鼠标距离边缘多少像素时开始滚动
EDGE_SCROLL_SPEED = 300  # 边缘滚动速度

# 默认字体（使用系统字体以支持中文）
import pygame
pygame.init()

# 尝试使用支持中文的字体
FONT_PATHS = [
    "C:/Windows/Fonts/simhei.ttf",  # Windows 黑体
    "/System/Library/Fonts/PingFang.ttc",  # macOS
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux
]

def get_font(size):
    """获取字体，优先使用支持中文的字体"""
    for font_path in FONT_PATHS:
        try:
            return pygame.font.Font(font_path, size)
        except:
            continue
    # 如果都失败，使用默认字体
    return pygame.font.Font(None, size)

# 颜色定义
COLOR_PLAYER = (0, 255, 0)
COLOR_ENEMY = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (100, 100, 100)
COLOR_YELLOW = (255, 255, 0)
COLOR_BLUE = (0, 100, 255)
COLOR_PURPLE = (255, 0, 255)
COLOR_ORANGE = (255, 165, 0)
COLOR_CYAN = (0, 255, 255)
COLOR_DARK_GRAY = (64, 64, 64)
COLOR_LIGHT_GRAY = (192, 192, 192)
COLOR_GOLD = (255, 215, 0)

# 游戏设置 - 调整为持久战
ENERGY_ATTACK_COST = 5  # 降低能量消耗
ENERGY_REPAIR_COST = 3  # 降低修理能量消耗
SP_GAIN_PER_ATTACK = 8  # 略微降低SP获取
MOTHERSHIP_SUPPLY_RANGE = 80
SUPPLY_RATE = 80  # 增加补给速度
SUPPLY_HP_RATE = 50  # 增加回血速度

# 战斗机行为设置
FIGHTER_AUTO_ATTACK_RANGE = 300  # 战斗机自动攻击范围
CIRCLE_STRAFE_RADIUS = 100  # 围绕攻击半径
CIRCLE_STRAFE_SPEED = 1  # 围绕速度

# 评分系统
SCORE_BASE_VICTORY = 1000  # 胜利基础分
SCORE_TIME_BONUS_MAX = 500  # 最大时间奖励
SCORE_TIME_TARGET = 300  # 目标时间（秒）
SCORE_UNIT_SURVIVAL = 100  # 每个存活单位的分数
SCORE_ENEMY_DEFEAT = 50  # 击败敌人的分数
SCORE_PERFECT_VICTORY = 1000  # 完美胜利奖励
SCORE_MOTHERSHIP_SURVIVAL = 500  # 母舰存活奖励

# 攻击类型
from enum import Enum

class AttackType(Enum):
    MELEE = "melee"          # 近战
    RANGED = "ranged"        # 远程
    ARTILLERY = "artillery"   # 炮击
    BEAM = "beam"            # 光束
    MISSILE = "missile"      # 导弹

# 单位类型
class UnitType(Enum):
    MOTHERSHIP = "mothership"    # 母舰
    FIGHTER = "fighter"          # 战斗机
    REPAIR = "repair"            # 修理机
    HEAVY = "heavy"              # 重型单位
    SCOUT = "scout"              # 侦察机
    BOMBER = "bomber"            # 轰炸机
    INTERCEPTOR = "interceptor"  # 拦截机

# 技能类型
class SkillType(Enum):
    DAMAGE_AOE = "damage_aoe"        # 范围伤害
    HEAL_AOE = "heal_aoe"            # 范围治疗
    BUFF_SPEED = "buff_speed"        # 速度加成
    BUFF_ATTACK = "buff_attack"      # 攻击加成
    SHIELD = "shield"                # 护盾
    TELEPORT = "teleport"            # 传送
    DISABLE = "disable"              # 禁用敌人
    REPAIR_ALL = "repair_all"        # 全体修理

# 命令模式
class CommandMode(Enum):
    NORMAL = "normal"        # 正常模式
    SELECTING_TARGET = "selecting_target"  # 选择目标模式

# 地形类型
class TerrainType(Enum):
    EMPTY = "empty"
    ASTEROID = "asteroid"        # 小行星（可破坏）
    DEBRIS = "dbrise"           # 碎片
    BARRIER = "barrier"         # 能量屏障（可破坏）
    CRYSTAL = "crystal"         # 水晶（装饰）