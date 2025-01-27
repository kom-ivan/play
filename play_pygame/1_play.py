import pygame
import random
import os

# --- Инициализация Pygame ---
pygame.init()
# --- Настройки игры ---
WIDTH, HEIGHT = 800, 600
FPS = 60
# --- Цвета ---
WHITE = pygame.color.THECOLORS['white']
# --- Пути к файлам ---
CAR_IMAGE_PATH = "car.png"
BACKGROUND_IMAGE_PATH = "zemla.png"
COIN_IMAGE_PATH = "coin.png"
TREE_IMAGE_PATH = "tree.png"
STONE_IMAGE_PATH = "stone.png"
PARTICLE_IMAGE_PATH = "particle1.png"
MENU_BACKGROUND_IMAGE_PATH = "menu.png" # Добавлен путь к фону меню
RESULT_FILE = "result.txt"
# --- Размеры машинки ---
CAR_SIZE = 80
# --- Размеры препятствий ---
TREE_SIZE = 150
STONE_SIZE = 60
COIN_SIZE = 60, 40
# --- Состояния игры ---
GAME_STATE_MENU = 0
GAME_STATE_PLAY = 1
GAME_STATE_PAUSE = 2
GAME_STATE_GAME_OVER = 3
# --- Прочие настройки ---
scroll_y = 0
score = 0
game_state = GAME_STATE_MENU
previous_score = 0
high_score = 0
all_coins = 0
collected_coins = 0
score_timer = 0
score_interval = 500 # 0.5 секунды #начисление счета
start_time = 0
previous_time = 0
pause_time = 0
# --- Создание окна ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Гонка")
clock = pygame.time.Clock()

# --- Загрузка изображений ---
def load_image(image_path, color_key=None):
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Файл не найден: {image_path}")
        if image_path.lower().endswith((".png", ".gif", ".bmp")):
            image = pygame.image.load(image_path).convert_alpha()
        else:
            image = pygame.image.load(image_path).convert()
        if color_key is not None:
            if color_key == -1:
                color_key = image.get_at((0, 0))
            image.set_colorkey(color_key)
        return image
    except (pygame.error, FileNotFoundError) as e:
        print(f"Ошибка загрузки изображения: {e}")
        pygame.quit()
        exit()

car_image = pygame.transform.scale(load_image(CAR_IMAGE_PATH), (CAR_SIZE, CAR_SIZE))
background_image = load_image(BACKGROUND_IMAGE_PATH)
background_rect = background_image.get_rect()
coin_image = pygame.transform.scale(load_image(COIN_IMAGE_PATH), COIN_SIZE)
tree_image = load_image(TREE_IMAGE_PATH)
stone_image = load_image(STONE_IMAGE_PATH)
menu_background_image = load_image(MENU_BACKGROUND_IMAGE_PATH)  # Загрузка фона меню
menu_background_rect = menu_background_image.get_rect()

# --- Класс машинки ---
class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = car_image
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rect.x -= 5
        if keys[pygame.K_d]:
            self.rect.x += 5
        self.rect.clamp_ip(screen.get_rect())

# --- Класс препятствий ---
class Obstacle(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-HEIGHT, -self.rect.height)
        self.speed_y = 7
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()

# --- Класс дерева ---
class Tree(Obstacle):
    def __init__(self, size=TREE_SIZE):
        scaled_image = pygame.transform.scale(tree_image, (size, size))
        super().__init__(scaled_image)

# --- Класс камня ---
class Stone(Obstacle):
    def __init__(self, size=STONE_SIZE):
        scaled_image = pygame.transform.scale(stone_image, (size, size))
        super().__init__(scaled_image)

# --- Класс монетки ---
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = coin_image
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-HEIGHT, -self.rect.height)
        self.speed_y = 5

    def update(self):
        self.rect.y += self.speed_y
        if self.rect.top > HEIGHT:
            self.kill()

# --- Класс управления препятствиями ---
class ObstacleManager:
    def __init__(self, all_sprites, obstacles, coins):
        self.all_sprites = all_sprites
        self.obstacles = obstacles
        self.coins = coins
        self.obstacle_timer = 0
        self.obstacle_interval = 900 #частота препятсвий (чем больше значение тем меньше появлений) меньше 900 не ставить
        self.coin_timer = 0
        self.coin_interval = 3000 #частота появления монет

    def create_obstacle(self):
        while True:
            obstacle_type = random.choice([Tree, Stone])
            obstacle = obstacle_type()
            if not any(abs(obstacle.rect.centerx - obs.rect.centerx) < 100 for obs in self.obstacles):
                break
        self.all_sprites.add(obstacle)
        self.obstacles.add(obstacle)

    def create_coin(self):
        while True:
            coin = Coin()
            if not any(abs(coin.rect.centerx - c.rect.centerx) < 100 for c in self.coins):
                break
        self.all_sprites.add(coin)
        self.coins.add(coin)

    def update(self):
        self.obstacle_timer += clock.get_time()
        if self.obstacle_timer >= self.obstacle_interval:
            self.create_obstacle()
            self.obstacle_timer = 0
        self.coin_timer += clock.get_time()
        if self.coin_timer >= self.coin_interval:
            self.create_coin()
            self.coin_timer = 0

# --- Функция проверки столкновений на основе маски ---
def mask_collide(sprite1, sprite2):
    offset_x = sprite2.rect.x - sprite1.rect.x
    offset_y = sprite2.rect.y - sprite1.rect.y
    return sprite1.mask.overlap(sprite2.mask, (offset_x, offset_y)) is not None

# --- Функция отрисовки кнопок ---
def draw_button(text, x, y, font_size, surface, color=WHITE, draw_rect=False):
    font = pygame.font.Font(None, font_size)
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=(x, y))
    surface.blit(text_surf, text_rect)
    if draw_rect:
        pygame.draw.rect(surface, color, (text_rect.left - 10, text_rect.top - 10, text_rect.width + 20, text_rect.height + 20), 2)
    return text_rect

# --- Функция проверки столкновений с препятствиями ---
def check_obstacle_collisions(car, obstacles):
    global all_coins, collected_coins, game_state
    collision = any(mask_collide(car, obs) for obs in obstacles)
    if collision:
        all_coins += collected_coins
        game_state = GAME_STATE_GAME_OVER
    return collision

def check_coins_collision(car, coins):
    global score, collected_coins
    collected = pygame.sprite.spritecollide(car, coins, True)
    score += len(collected) * 10
    collected_coins += len(collected)
    return collected

# --- Загрузка данных ---
def load_data():
    try:
        if os.path.exists(RESULT_FILE):
            with open(RESULT_FILE, "r") as file:
                lines = file.readlines()
                if len(lines) == 4:
                   return int(lines[0].strip()), int(lines[1].strip()), int(lines[2].strip()), int(lines[3].strip())
    except Exception:
        pass
    return 0, 0, 0, 0

# --- Сохранение данных ---
def save_data():
    try:
        with open(RESULT_FILE, "w") as file:
            file.write(str(high_score) + '\n')
            file.write(str(previous_score) + '\n')
            file.write(str(all_coins) + '\n')
            file.write(str(previous_time))
    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")

# --- Загрузка данных при запуске игры ---
high_score, previous_score, all_coins, previous_time = load_data()


# --- Класс Particle ---
gravity = 0.25
screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)

class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image(PARTICLE_IMAGE_PATH)]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_particles)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость - это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой
        self.gravity = gravity

    def update(self):
        # применяем гравитационный эффект: 
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()
    
    def draw(self, surface):
        if screen_rect.collidepoint(self.rect.center):
            surface.blit(self.image, self.rect)

def create_particles(position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))

# --- Группы спрайтов ---
all_sprites = pygame.sprite.Group()
obstacles = pygame.sprite.Group()
coins = pygame.sprite.Group()
all_particles = pygame.sprite.Group() # Добавлено

# --- Создание машинки ---
car = Car()
all_sprites.add(car)

# --- Создание менеджера препятствий ---
obstacle_manager = ObstacleManager(all_sprites, obstacles, coins)


def draw_pause_button(paused):
    return draw_button("Пауза" if paused else "||", WIDTH - 50, 30, 30, screen, draw_rect=False)

def draw_pause_menu():
    continue_rect = draw_button("Продолжить", WIDTH // 2, HEIGHT // 2 - 100, 40, screen, draw_rect=True)
    restart_rect = draw_button("Начать заново", WIDTH // 2, HEIGHT // 2 - 30, 40, screen, draw_rect=True)
    menu_rect = draw_button("Выйти в меню", WIDTH // 2, HEIGHT // 2 + 40, 40, screen, draw_rect=True)
    return continue_rect, restart_rect, menu_rect

def draw_game_over():
    restart_rect = draw_button("Начать заново", WIDTH // 2, HEIGHT // 2 + 20, 50, screen, draw_rect=True)
    menu_rect = draw_button("Выйти в меню", WIDTH // 2, HEIGHT // 2 + 80, 50, screen, draw_rect=True)
    return restart_rect, menu_rect

def draw_background():
    for background_row in range(-1, HEIGHT // background_rect.height + 2):
        screen.blit(background_image, (0, background_row * background_rect.height - scroll_y))

def draw_score():
    global collected_coins
    font = pygame.font.Font(None, 30)
    text_coins = font.render(f"Собрано монет: {collected_coins}", True, WHITE)
    screen.blit(text_coins, (10, 10))
    draw_button(f"Счет: {score}", WIDTH // 2, 30, 40, screen, draw_rect=False)
    
    if game_state == GAME_STATE_PLAY:
      minutes = (pygame.time.get_ticks() - start_time) // 60000
      seconds = ((pygame.time.get_ticks() - start_time) // 1000) % 60
      timer_text = font.render(f"{minutes:02}:{seconds:02}", True, WHITE)
      timer_rect = timer_text.get_rect(center=(WIDTH // 2 + 150, 30))
      screen.blit(timer_text, timer_rect)
      
def draw_menu():
    global previous_score, all_coins, previous_time
    
    # Масштабирование изображения для полного покрытия экрана
    menu_bg_scaled = pygame.transform.scale(menu_background_image, (WIDTH, HEIGHT))
    menu_bg_rect = menu_bg_scaled.get_rect()
    
    # Вычисление координат для центрирования
    menu_bg_rect.center = (WIDTH // 2, HEIGHT // 2)
        
    screen.blit(menu_bg_scaled, menu_bg_rect) # Отрисовка фона
    
    font = pygame.font.Font(None, 30)
    minutes = previous_time // 60
    seconds = previous_time % 60
    text_prev_score = font.render(f"Предыдущий результат: {previous_score} ({minutes:02}:{seconds:02})", True, WHITE)
    text_high_score = font.render(f"Рекорд: {high_score}", True, WHITE)
    text_all_coins = font.render(f"Всего монет: {all_coins}", True, WHITE)
    screen.blit(text_prev_score, text_prev_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))
    screen.blit(text_high_score, text_high_score.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))
    screen.blit(text_all_coins, text_all_coins.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
    start_button_rect = draw_button("Начать игру", WIDTH // 2, HEIGHT // 2 + 50, 50, screen, draw_rect=True)
    exit_button_rect = draw_button("Выйти из игры", WIDTH // 2, HEIGHT // 2 + 120, 50, screen, draw_rect=True)
    return start_button_rect, exit_button_rect

# --- Функция для перезапуска игры ---
def restart_game():
    global scroll_y, score, previous_score, collected_coins, start_time, pause_time
    previous_score = score
    scroll_y = 0
    score = 0
    collected_coins = 0
    start_time = pygame.time.get_ticks()
    pause_time = 0
    all_sprites.empty()
    obstacles.empty()
    coins.empty()
    all_particles.empty() # Очистка всех частиц
    car.rect.midbottom = (WIDTH // 2, HEIGHT - 20)
    all_sprites.add(car)

# --- Основной цикл игры ---
running = True
while running:
    # --- Обработка событий ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            save_data()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if game_state == GAME_STATE_MENU:
                if menu_button_rect[0].collidepoint(mouse_pos):
                    game_state = GAME_STATE_PLAY
                    start_time = pygame.time.get_ticks() - pause_time
                elif menu_button_rect[1].collidepoint(mouse_pos):
                    running = False
                    save_data()
            elif game_state == GAME_STATE_PLAY:
                if pause_button_rect.collidepoint(mouse_pos):
                    game_state = GAME_STATE_PAUSE
                    pause_time = pygame.time.get_ticks() - start_time
                create_particles(event.pos) # Создание частиц при клике в игровом состоянии
            elif game_state == GAME_STATE_PAUSE:
                if continue_button_rect.collidepoint(mouse_pos):
                    game_state = GAME_STATE_PLAY
                    start_time = pygame.time.get_ticks() - pause_time
                elif restart_button_rect.collidepoint(mouse_pos):
                    game_state = GAME_STATE_PLAY
                    restart_game()
                elif menu_button_pause_rect.collidepoint(mouse_pos):
                    game_state = GAME_STATE_MENU
                    all_coins += collected_coins
                    restart_game()
            elif game_state == GAME_STATE_GAME_OVER:
                if game_over_button_rect[0].collidepoint(mouse_pos):
                     game_state = GAME_STATE_PLAY
                     restart_game()
                elif game_over_button_rect[1].collidepoint(mouse_pos):
                    game_state = GAME_STATE_MENU
                    restart_game()

    # --- Обновление игры ---
    if game_state == GAME_STATE_PLAY:
        last_scroll_y = scroll_y
        scroll_speed = 2
        scroll_y -= scroll_speed * clock.get_time() / 16.666
        if scroll_y < -background_rect.height:
           scroll_y = 0
        score_timer += clock.get_time()
        if score_timer >= score_interval:
            score += 1
            score_timer = 0
        if score > high_score:
            high_score = score
        check_coins_collision(car,coins)
        all_sprites.update()
        obstacle_manager.update()
        if check_obstacle_collisions(car, obstacles):
            game_state = GAME_STATE_GAME_OVER
            previous_time = (pygame.time.get_ticks() - start_time) // 1000

    # --- Отрисовка ---
    #screen.fill(BLACK)
    if game_state == GAME_STATE_MENU:
        menu_button_rect = draw_menu()
    elif game_state == GAME_STATE_PLAY:
        draw_background()
        for particle in all_particles:
            particle.draw(screen) # Отрисовка частиц
        all_sprites.draw(screen)
        draw_score()
        pause_button_rect = draw_pause_button(False)
        all_particles.update() # Обновление частиц
    elif game_state == GAME_STATE_PAUSE:
        draw_background()
        for particle in all_particles:
            particle.draw(screen)
        all_sprites.draw(screen)
        pause_button_rect = draw_pause_button(True)
        continue_button_rect, restart_button_rect, menu_button_pause_rect = draw_pause_menu()
    elif game_state == GAME_STATE_GAME_OVER:
       draw_background()
       for particle in all_particles:
           particle.draw(screen)
       all_sprites.draw(screen)
       game_over_button_rect = draw_game_over()


    pygame.display.flip()
    clock.tick(FPS)

# --- Сохранение данных перед выходом ---
save_data()

# --- Выход ---
pygame.quit()
