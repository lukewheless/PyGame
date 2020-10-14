import sys
from time import sleep

import pygame
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button

from ship import Ship
from bullet import Bullet
from alien import Alien

class AlienInvasion:
    #overall class to manage game assets and behavior

    def __init__(self):
        #initialize the game, and create game resources
        pygame.init()
        self.settings = Settings()

        self.screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width 
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption('Alien Invasion')

        #create instance to store game stats and create scoreboard
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.alien = pygame.sprite.Group()

        self._create_fleet()

        self.play_button = Button(self, "Play") #creates instance but doesn't draw button

    def run_game(self):
        #start the main loop for the game
        while True:
            self._check_events()

            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
            
            self._update_screen()
            
    def _check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keydown_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos() #returns tuple w/ mouse cursor's x & y cords when mouse is clicked, send to next method
                self.check_play_button(mouse_pos)
    
    def _check_play_button(self, mouse_pos):
        #start new game when user clicks play and when game is not active
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            #reset game settings (including speed)
            self.settings.initialize_dynamic_settings()

            #reset game stats
            self.stats.reset_stats()
            self.stats.game_active = True 
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            #get rid of remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            #create new fleet and center ship
            self._create_fleet()
            self.ship.center_ship()

            #hide mouse cursor
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self,event):
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyup_events(self,event):          
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _fire_bullet(self):
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(elf)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        #update position of bullets and get rid of old bullets
        self.bullets.update()

        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        #respond to bullet-alien collisions    
        #check for any bullets that have hit alien, get rid of both if hit
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        if collisions: #update score when alien is shot down
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score() #updating collisions dict with score
            self.sb.check_high_score()

        if not self.aliens:
            #destroy existing bullets and create new fleet once fleet is destroyed
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed() #increase tempo when last alien in fleet has been shot down

            #increase level
            self.stats.level += 1
            self.sb.prep_level()

    def _update_aliens(self):
        #update position of all aliens in fleet after checking if it hits the edge
        self._check_fleet_edges()
        self.aliens.update()

        #look for alien-ship collisions
        if pygame.sprite.spritecollideany(self.ship, self.aliens): #uses sprite and group to loop and find collisions
            self._self_hit()

        #look for aliens hitting bottom
        self._check_aliens_bottom()

    def _ship_hit(self):
        #respond to ship being hit by an alien
        if self.stats.ships_left >= 0:
            #decrement ships_left and update scoerboard
            self.stats.ships_left -= 1
            self.sb.prep_ships()

            #get rid of remaining aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            #create new fleet and center ship
            self._create_fleet()
            self.ship.center_ship()

            #pause
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True) #makes mouse cursor visible again once game is over

    def _create_fleet(self):
        #create fleet of aliens

        #make alien and find aliens in a row w/ equal spacing
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien_width = alien.rect.width
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        #determine number of rows of aliens that fit onto screen
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        #create full fleet of aliens
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number):
        #create alien and place in row
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        #respond if aliens hit edge
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        #drop entire fleet and change direction
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        #check if any aliens reach bottom of screen
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                #as if ship got hit
                self._ship_hit()
                break

    def _update_screen(self):
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        #draw score info
        self.sb.show_score()

        #draw the play button if game is inactive
        if not self.stats.game_active:
            self.play_button.draw_button()

        pygame.display.flip()

    if __name__ == '__main__':
        #make a game instance, and run the game
        ai = AlienInvasion()
        ai.run_game()