import pygame
import os

class SpriteManager:
    def __init__(self):
        self.sprites = {}
        self.default_size = (40, 40)
        
    def load_sprite(self, name, path):
        """加载精灵图片"""
        try:
            if os.path.exists(path):
                image = pygame.image.load(path).convert_alpha()
                self.sprites[name] = image
                print(f"Loaded sprite: {name} from {path}")
                return True
            else:
                print(f"Sprite file not found: {path}")
                return False
        except Exception as e:
            print(f"Failed to load sprite {name}: {e}")
            return False
            
    def get_sprite(self, name, size=None):
        """获取精灵，如果没有则返回None"""
        if name in self.sprites:
            sprite = self.sprites[name]
            if size:
                sprite = pygame.transform.scale(sprite, size)
            return sprite
        return None