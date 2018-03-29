# The reason fonts are defined outside of game_constants.py
# is that we need to initialize pygame.font before defining them.

import pygame

FONT_LARGE = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 60)
FONT_MEDIUM = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 36)
FONT_SMALL = pygame.font.Font(pygame.font.match_font('consolas', bold=True), 16)
