import pygame
import csv
import time
import random
import os


''' 
This script runs the single-player Pong that is controlled with EMG signals.
The structure of the game is inspired from this link https://www.youtube.com/watch?v=Q94blhLEe1c&t=1s&ab_channel=CodingwithRonak  
'''


# --- initalize game using pygame ---
pygame.init()

# --- frames per seconds ---
FPS = pygame.time.Clock()
# --- set the size of the window ---
WIN = pygame.display.set_mode((800,800))
# --- set title of the window that pops up when running the script ---
pygame.display.set_caption('Single player Pong')

# --- asks for player name ---
player_name = input("Name of player: ")
# --- asks for number of play ---
number_of_play = input("Number of play: ")

# --- asks if the player has feedback or not, to document into highscore file ---
feedback_type = input("Does user have feedback? y/n: ")

# --------------------- UPDATE VALUES HERE that are found from running MVC_plot.py ---------------------
MVC_M1 = 231
MVC_M2 = 231
# scaled MVC
MVC_M1_SCALED = MVC_M1 * 0.8
MVC_M2_SCALED = MVC_M2 * 0.8
# ---------------------------------------------------------------

flag_user = True
time_flag = False
reset_value = 0

# ----- COLORS of objects in game ----
Black = (0,0,0)
White = (255,255,255)
Red = (255,0,0)

# ---- middle for player stick ----
MIDDLE = 325
# ---- Initial speed of player ----
# --- moves 3.2 pixels per target value ---
S = 3.2

# ---- Initial speed of ball ----
ball_x = 2
ball_y = 2 


player_score = 0
# ---- SET TEXT FONT FOR SCREEN ----
game_font_highscore = pygame.font.Font('freesansbold.ttf', 20)
game_font_muscles = pygame.font.Font('freesansbold.ttf', 80)

# ---- location and width of ball and player ----
Player = pygame.Rect(750, MIDDLE, 10, 150)
# ---- determining the starting position of the ball and direction of movement ----
dir_list = [-1, 1]
dir = random.choice(dir_list)
if dir == 1:
    rand_num = random.randint(300,750)
else:
    rand_num = random.randint(50,500)

Ball = pygame.Rect(200,rand_num,15,15)
# ---- red stick ----
red_Stick = pygame.Rect(780, 400, 10, 0)


# ---- RST button ----
button = pygame.image.load('reset.png')
BUTTON_SIZE = (100,40)

# --- the image for the reset button, scaled ----
RESET_button = pygame.transform.scale(button, BUTTON_SIZE)
BUTTON_POS = (0,0)

def draw():
    ''' 
    A function that draws the frame of the game. Is set to 60 frames per second.
    Updates the movement of the ball, player and red stick    
    '''
    # 60 frames per sec
    FPS.tick(60)
    WIN.fill(Black)
    pygame.draw.rect(WIN, White,Player)
    pygame.draw.rect(WIN, Red, red_Stick)
    pygame.draw.ellipse(WIN, White,Ball)
    WIN.blit(RESET_button, BUTTON_POS)



def Player_Border():
    ''' 
    A function that sets the border for the player, so that the player does not move out of the window.
    '''
    if Player.y >= 645:
        S = 0
        Player.y = 644
    if Player.y <= 5:
        S = 0
        Player.y = 6

def normalise(signal1, signal2):
    ''' 
    A function that normalises the raw EMG signals read from the panda
    returns the normalised values for front and back muscle
    '''
    s1_normal = int(signal1/MVC_M1_SCALED *100)
    if s1_normal > 100:
        s1_normal = 100
    s2_normal = int(signal2/MVC_M2_SCALED *100)
    if s2_normal > 100:
        s2_normal = 100

    return s1_normal, s2_normal
    
def move_player(player_score):
    ''' 
    A function that reads the EMG signals from the shared file, 
    processes the signals and moves the player according to the values.
    The effect of the co-contraction is determined as well.
    '''
    # Read the values from the raw signals file
    with open("shared_values_raw.csv", "r") as file:
        lines = file.readlines()

    # Extract the values
    raw_m1 = int(lines[-2].strip())
    raw_m2 = int(lines[-1].strip())

    # normalise the raw signals
    normal_m1, normal_m2 = normalise(raw_m1, raw_m2)

    # save the raw signals
    with open(f"EMG_Users\{player_name}_{number_of_play}_rst{reset_value}.csv", 'a', newline='') as file:
        writer = csv.writer(file)
        check_file = os.path.getsize(f"EMG_Users\{player_name}_{number_of_play}_rst{reset_value}.csv")

        if check_file == 0:
            # Writing the header
            writer.writerow(["M1","M2"])
            writer.writerow(["MVC",MVC_M1,"MVC", MVC_M2])
        else:
            # Writing the raw signals
            # print(time.time())
            writer.writerow([raw_m1, raw_m2])


    if player_score <= 20:
        if player_score == 0:
            player_score = 1
        # --- calculating the percentage of co-contraction effect. Increases by 5% per player score ---
        co_con_value = (player_score * 5) / 100.0
        #  M1 > M2
        if normal_m1 >= normal_m2:
            signal_diff = normal_m1 - (co_con_value*normal_m2)
        else: # M1 < M2
            signal_diff = (co_con_value*normal_m1) - normal_m2
    # --- weight of muscle co-contraction = 100% ---
    else: 
        signal_diff = normal_m1 - normal_m2

    return signal_diff, normal_m1, normal_m2


# --- Main loop that runs when the script is runned ---
while True:
    while flag_user == True:
        # --- print input answers from user and save into file ---
        if feedback_type == "y" or feedback_type == "Y":
            feedback_type = "feedback"
            print(f"{player_name} has feedback")
            flag_user = False
        elif feedback_type == "n" or feedback_type == "N":
            feedback_type = "no"
            print(f"{player_name} has no feedback")
            flag_user = False
        else:
            print("feedback input is invalid, please press y or n: ")
            feedback_type = input(f"Try again, does {player_name} have feedback? y/n: ")
        # --- write name of player, number of play, with/without feedback into score.csv ---
        with open('scores.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([player_name, "Number of play:", number_of_play ,feedback_type])

    # --- events in the pygame ---
    for event in pygame.event.get():
        start_time = time.time()
        if event.type == pygame.QUIT:
            pygame.quit()
            time.sleep(2)
            print(f"{player_name} highscore is: {player_score}")
            # --- write high score to file ---
            with open('scores.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([player_score])
            exit()

        
        # --- if a mouse is clicked on (restart) ----
        if event.type == pygame.MOUSEBUTTONDOWN:
            ra, rb = event.pos 
            if RESET_button.get_rect().collidepoint(ra,rb):
                # ---- write highscore to csv file ----
                with open('scores.csv', 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([player_score])
                # --- update reset value ---
                reset_value += 1
                # ----- resetting values of ball and player and red stick ----
                dir = random.choice(dir_list)
                if dir == 1:
                    rand_num = random.randint(300,750)
                else:
                    rand_num = random.randint(50,500)
                Ball.x = 200
                Ball.y = rand_num
                Player.x = 750
                Player.y = MIDDLE
                ball_x = 2
                ball_y = 2
                S = 3.2
                red_Stick.update(780, 400, 10, 2)
                print(f"{player_name} highscore is: {player_score}")
                player_score = 0
        

    # ---- Controlling the player ----
    # m_s1: muscle_signal1, m_s2: muscle_signal2
    signal_diff, m_s1, m_s2 = move_player(player_score)
    # print(signal_diff)
    if signal_diff > 0: #move to the right
        target_val = MIDDLE + (signal_diff*S)
        Player.y = target_val
        red_Stick.update(780, 400, 10, signal_diff*S*1.22)
    elif signal_diff < 0: #move to the left
        target_val = MIDDLE + (signal_diff*S)
        Player.y = target_val
        red_Stick.update(780, 400,10, signal_diff*S*1.22)
        red_Stick.normalize()
    else:
        pass

    # ------- MOVING THE BALL -----
    Ball.x += ball_x
    Ball.y += ball_y * dir

    if Ball.top <= 0 or Ball.bottom >= 800:
        ball_y *= -1
    if Ball.left <= 0 or Ball.right >= 800:
        ball_x *= -1

    # --- get current time in seconds ---
    # collide_time = time.time()
    # print(collide_time)


    if Ball.colliderect(Player):
        time_flag = True
        collide_time = time.time()
        # print(f"interval of ball touching player is: {collide_time - start_time} seconds")
        # wait for 400 ms to increase high score

        # print(f"current time: {current_time}")
        ball_x *= -1
    

    if time_flag == True and (time.time()-collide_time) > 0.4:
        player_score += 1
        # ---- increase speed of ball if high score > 20 ----
        if player_score > 20:
            ball_y = 1.1*ball_y
            ball_x = 1.1*ball_x

        time_flag = False


    # --- if ball touches the bottom floor, the game stops ----
    if Ball.x >= 780:
        ball_y = 0
        ball_x = 0
        S = 0

    draw()
    Player_Border()

    # --- modify high score value and normalized muscle values ---
    player_text = game_font_highscore.render(f"high score: {player_score}", False, White)
    muscle_left = game_font_muscles.render(f"{m_s2}", False, Red)
    muscle_right = game_font_muscles.render(f"{m_s1}", False, Red)


    # --- blit = display high-score text to Window
    WIN.blit(player_text, (340,50))
    # --- display normalized muscle values ----
    WIN.blit(muscle_left, (200,100))
    WIN.blit(muscle_right, (200,650))

    # ---- draw the game screen and update ----
    pygame.display.update()

