from win32con import ENUM_CURRENT_SETTINGS
from win32api import EnumDisplaySettings
import serial
import pygame
import time
import numpy
import serial.tools.list_ports
import pygame_gui
import os
import webbrowser
# do not delete this eventhough it is not used, for some reason it increases the render quality
from pyautogui import press

# makes the current directory the file's one
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pygame.init()

timer = pygame.time.Clock()
dev_mode = EnumDisplaySettings(None, ENUM_CURRENT_SETTINGS)  # get the fps OS setting
timer.tick(dev_mode.DisplayFrequency)  # fps of the window
# fps config for pygame_gui
UI_REFRESH_RATE = timer.tick(dev_mode.DisplayFrequency)/1000

info = pygame.display.Info()
screen_height = info.current_h
screenratio = 1.05  # 1.5 is the ratio screen/window
height = round(screen_height/screenratio)
width = height*(1920/1440)
screen = pygame.display.set_mode([width, height])

# creating manager of text inputs
manager = pygame_gui.UIManager((width, height))
text_input_x = text_input_y = text_input_z = False

rect_x = pygame.Rect((width/5, height/16.5), (80, 22))
rect_y = pygame.Rect((width/5, height/11.3), (80, 22))
rect_z = pygame.Rect((width/5, height/8.62), (80, 22))


def create_inputs():  # creating the text inputs
    global text_input_x
    global text_input_y
    global text_input_z

    text_input_x = pygame_gui.elements.UITextEntryLine(relative_rect=rect_x, manager=manager, object_id="x_entry")
    text_input_x.set_text("Type X")
    text_input_y = pygame_gui.elements.UITextEntryLine(relative_rect=rect_y, manager=manager, object_id="y_entry")
    text_input_y.set_text("Type Y")
    text_input_z = pygame_gui.elements.UITextEntryLine(relative_rect=rect_z, manager=manager, object_id="z_entry")
    text_input_z.set_text("Type Z")


active_input = 0


def clearinput(which=active_input):
    if (which == 0):
        text_input_x.set_text("")
        text_input_x.focus()
    elif (which == 1):
        text_input_y.set_text("")
        text_input_y.focus()
    elif (which == 2):
        text_input_z.set_text("")
        text_input_z.focus()


precision_c = 1.4  # inverse of dpi (in practical sense)

# the name of the window
pygame.display.set_caption("Robotic Arm (by Emilio Reato)")
icon_image = pygame.image.load("icon.png").convert_alpha()
pygame.display.set_icon(icon_image)
background_image = pygame.image.load("background.png").convert()
background_image = pygame.transform.smoothscale(background_image, (width, height))
img_connect0 = pygame.image.load("img_connect0.png").convert_alpha()
img_connect0 = pygame.transform.smoothscale(img_connect0, (width, height))
img_connect1 = pygame.image.load("img_connect1.png").convert_alpha()
img_connect1 = pygame.transform.smoothscale(img_connect1, (width, height))
img_connect2 = pygame.image.load("img_connect2.png").convert_alpha()
img_connect2 = pygame.transform.smoothscale(img_connect2, (width, height))
img_connect0_dot = pygame.image.load("img_connect0_dot.png").convert_alpha()
img_connect0_dot = pygame.transform.smoothscale(img_connect0_dot, (width, height))
coordinates = pygame.image.load("coordinates.png").convert_alpha()
coordinates = pygame.transform.smoothscale(coordinates, (width, height))
notfound = pygame.image.load("notfound.png").convert_alpha()
notfound = pygame.transform.smoothscale(notfound, (width, height))
crosshair = pygame.image.load("crosshair.png").convert_alpha()
crosshair = pygame.transform.smoothscale(crosshair, (height/40, height/40))
crosshair_alt = pygame.image.load("crosshair_alt.png").convert_alpha()
crosshair_alt = pygame.transform.smoothscale(crosshair_alt, (height/40, height/40))
clawmain = pygame.image.load("clawmain1.png").convert_alpha()
clawmain = pygame.transform.smoothscale(clawmain, (height/32, height/32))
clawright = pygame.image.load("clawright1.png").convert_alpha()
clawright = pygame.transform.smoothscale(clawright, (height/40, height/40))
clawleft = pygame.image.load("clawleft1.png").convert_alpha()
clawleft = pygame.transform.smoothscale(clawleft, (height/40, height/40))
claws_images_w, claws_images_h = clawleft.get_size()

font = pygame.font.SysFont("verdana", round(17/screenratio))  # fuente de texto

pygame.mouse.set_visible(False)  # both needed for set mouse in virtual mode
pygame.event.set_grab(True)

zlock = False
left = False
coord_x = 0
coord_y = 60
coord_z = 80
inserted_x = inserted_y = inserted_z = 0
claw = 0
format_mode_demo = 0
tempo = 0
tempo2 = time.time() * 1000
tempo3 = 0
connectionstate = 0
comunicate = True
show_coordinates = True
state_connection_even = False
state2 = False
state_for_inputs = False
blackcursor = True
arduinonotplugged = 0
permisionfor1s = 0
disconnectedonpurpose = False
notsendingtimeout = False
wasunplugged = False
writing = False
z_circle_position = width/15.25, numpy.interp(coord_z, [-50, 280], [height/1.615, height/13])
just_hiddden_coordinates = True


def connect(justcheckplugged=False):

    def get_ports():
        ports = serial.tools.list_ports.comports()
        return ports

    # function i took from github to automatically find the COM arduino is connected
    def findArduino(portsFound):
        commPort = 'None'
        numConnection = len(portsFound)
        for i in range(0, numConnection):
            port = foundPorts[i]
            strPort = str(port)
            if 'Arduino' in strPort:
                splitPort = strPort.split(' ')
                commPort = (splitPort[0])
        return commPort

    foundPorts = get_ports()
    connectPort = findArduino(foundPorts)

    global arduinonotplugged
    global permisionfor1s
    global comunicate

    if (connectPort != 'None'):
        arduinonotplugged = 0
        if (justcheckplugged == False):
            try:
                global arduino
                global connectionstate
                # opening serial port
                arduino = serial.Serial(connectPort, 19200)  # , timeout=2)
                screen.blit(img_connect1, (0, 0))
                connectionstate = 1
                comunicate = True

                if not arduino.is_open:
                    arduino.open()
            except:
                connectionstate = 0
                comunicate = False
                # print("Couldn't connect with Arduino through serial port")
    else:
        comunicate = False
        connectionstate = 0
        arduinonotplugged = 1
        if (justcheckplugged == False):
            permisionfor1s = 1

    return connectionstate


def disconnect():
    try:
        arduino.close()
        global connectionstate
        global comunicate
        connectionstate = 0
        comunicate = False
    except:
        pass


def send(value, sign):  # value -->int / sign -->byte character b'h'     //able to send negative numbers
    global connectionstate
    global notsendingtimeout
    global tempo3
    try:
        string_val = str(value)
        byte_val = string_val.encode()
        arduino.write(byte_val)
        connectionstate = 1
        arduino.write(sign)
    except serial.SerialTimeoutException:
        disconnect()
        # print("Timeouted in writing to arduino. Now disconnected")
    except:
        connectionstate = 2
        connect(True)
        if (arduinonotplugged == True):
            global wasunplugged
            global state
            state_connection_even = True
            wasunplugged = True
            disconnect()
        # print("Couldn't send data to Arduino through serial port")


def blitRotate(surf, image, pos, originPos, angle):  # code from github: how to rotate an image with a different center of rotation
    image_rect = image.get_rect(topleft=(pos[0] - originPos[0], pos[1]-originPos[1]))    # offset from pivot to center
    offset_center_to_pivot = pygame.math.Vector2(pos) - image_rect.center
    rotated_offset = offset_center_to_pivot.rotate(-angle)  # roatated offset from pivot to center
    rotated_image_center = (pos[0] - rotated_offset.x, pos[1] - rotated_offset.y)  # roatetd image center
    rotated_image = pygame.transform.rotate(image, angle)  # get a rotated image
    rotated_image_rect = rotated_image.get_rect(center=rotated_image_center)
    surf.blit(rotated_image, rotated_image_rect)  # rotate and blit the image


def is_number(cadena):  # it checks if its a number even considering floats
    try:
        float(cadena)
        return True
    except ValueError:
        return False

# SET UP


connect()
run = True
while run:

    millis = time.time() * 1000  # classic millis timer

    screen.blit(background_image, (0, 0))
    if (connectionstate == 1):
        screen.blit(img_connect1, (0, 0))
    elif (connectionstate == 0):
        screen.blit(img_connect0, (0, 0))
    else:
        screen.blit(img_connect2, (0, 0))
    if (show_coordinates):
        text1 = font.render("{0:.1f}".format(float(coord_x)), True, (37, 40, 42)).convert_alpha()
        screen.blit(text1, (width/6.2, height/15.6))
        text2 = font.render("{0:.1f}".format(float(coord_y)), True, (37, 40, 42)).convert_alpha()
        screen.blit(text2, (width/6.2, height/10.62))
        text3 = font.render("{0:.1f}".format(float(coord_z)), True, (37, 40, 42)).convert_alpha()
        screen.blit(text3, (width/6.2, height/8.15))
        screen.blit(coordinates, (0, 0))
        blitRotate(screen, clawleft, (width/6.72, height/5.208), (claws_images_w/1.5, claws_images_h/5.8), numpy.interp(claw, [0, 500], [-5, 48.5]))
        blitRotate(screen, clawright, (width/6.38, height/5.208), (claws_images_w/6, claws_images_h/6.35), numpy.interp(claw, [0, 500], [5, -48.5]))
        screen.blit(clawmain, (width/7.045, height/6.1))
        just_hiddden_coordinates = True
    """elif (just_hiddden_coordinates):
        try:
            text_input_x.kill()
            text_input_y.kill()
            text_input_z.kill()
            print("killed")
            pygame.mouse.get_rel()
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            state2 = False
            state_for_inputs = False
        except:
            pass
        just_hiddden_coordinates = False"""
    if (arduinonotplugged and permisionfor1s == 1):
        screen.blit(notfound, (0, 0))
    if (millis - 1500 > tempo2):
        tempo2 = millis
        permisionfor1s = 0

    # getting the movement and updating the position based on that
    if (not state2):
        xmove, ymove = pygame.mouse.get_rel()
        if (zlock == False):
            if (-280 < coord_x+(xmove/10)/precision_c < 280):
                coord_x += (xmove/10)/precision_c
            if (0 < coord_y-(ymove/10)/precision_c < 280):
                coord_y -= (ymove/10)/precision_c
            # translating the position to the screen's resolution
            # EL -HEIGHT/100 DE ACA ABAJO ME SUENA RARETE
            cursor_position = numpy.interp(coord_x, [-280, 280], [width/5.52, width/1.0908])-height / 100, numpy.interp(coord_y, [0, 280], [height/1.738,  height/11.81])-height/100

        elif (-50 < coord_z-(ymove/10)/precision_c < 280):
            coord_z -= (ymove/10)/precision_c
            z_circle_position = width/15.25, numpy.interp(coord_z, [-50, 280], [height/1.607, height/14.19])

    # print(str(coord_x) + "   " + str(coord_y) + "   " + str(coord_z) + " " + str(9))

    # showing the cursor and creating circle as a reference for Z
    if (blackcursor):
        screen.blit(crosshair, cursor_position)
    else:
        screen.blit(crosshair_alt, cursor_position)
    pygame.draw.circle(screen, pygame.Color(round(coord_z/(2.2/1.2)+50), round(coord_z/(2.2/(1.2*0.15))+50), 95), z_circle_position, 14/screenratio)

    if (millis - 8 > tempo):
        tempo = millis
        if (comunicate):
            send(round(numpy.interp(coord_x, [-280, 280], [0, 180])), b'a')
            send(round(numpy.interp(coord_y, [0, 280], [0, 180])), b'b')
            send(round(numpy.interp(coord_z, [-50, 280], [0, 180])), b'c')
            send(round(numpy.interp(claw, [0, 500], [0, 180])), b'd')
            send(format_mode_demo, b'e')
        format_mode_demo = "d"

    for event in pygame.event.get():  # when we get an event

        if (event.type == pygame.MOUSEMOTION):
            pass
        else:
            if event.type == pygame.KEYDOWN:  # if it was a key pressed

                # if a number was pressed save it, otherwise save "d"
                if (pygame.key.name(event.key)[len(pygame.key.name(event.key)) // 2].isnumeric()):
                    if (state_for_inputs and writing):
                        clearinput(active_input)
                        writing = False
                    else:
                        format_mode_demo = int(pygame.key.name(event.key)[len(pygame.key.name(event.key)) // 2])
                else:
                    format_mode_demo = "d"  # defult

                if (pygame.key.name(event.key) == "escape"):  # and if it was the key "escape"
                    run = False
                elif (pygame.key.name(event.key) == "tab"):  # and if it was the key "escape"
                    if (not arduinonotplugged and not wasunplugged):
                        state_connection_even = not state_connection_even  # juego de estados que termina funcionando pero confuso
                    else:
                        state_connection_even = True
                    if (state_connection_even and arduinonotplugged == False):
                        wasunplugged = False
                        disconnect()
                    else:
                        connect()
                elif (pygame.key.name(event.key) == "left ctrl"):
                    show_coordinates = True
                    state_for_inputs = not state_for_inputs
                    if (state_for_inputs):
                        create_inputs()
                        active_input = 0
                        writing = True
                        state2 = True
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        text_input_x.focus()
                    else:
                        text_input_x.kill()
                        text_input_y.kill()
                        text_input_z.kill()
                        pygame.mouse.get_rel()
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        state2 = False
                elif (pygame.key.name(event.key) == "left alt"):  # and if it was the key "escape"
                    state2 = not state2
                    if (state2):
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                    else:
                        pygame.mouse.get_rel()
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)

                elif (pygame.key.name(event.key) == "left shift"):  # and if it was the key "escape"
                    show_coordinates = not show_coordinates
                elif (pygame.key.name(event.key) == "space"):  # and if it was the key "escape"
                    if (connectionstate == 1 or connectionstate == 2):
                        connectionstate = 2
                        comunicate = not comunicate
                elif (pygame.key.name(event.key) == "f2"):
                    webbrowser.open(
                        "https://github.com/emilioreato/emilioreato.git")

                # if (writing == True and not pygame.key.name(event.key) == "left ctrl"):
                #    clearinput()
                #    writing = False

                # print(pygame.key.name(event.key))

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up -->claw++
                    claw += (500/(precision_c*15))
                    if (claw > 500):
                        claw = 500
                elif event.button == 5:  # Scroll down -->claw--
                    claw -= (500/(precision_c*15))
                    if (claw < 0):
                        claw = 0
                elif event.button == 1:
                    if (state_for_inputs):  # placeholder for text inputs disappears on left click
                        if rect_x.collidepoint(event.pos):
                            clearinput(0)
                            text_input_x.focus()
                            text_input_y.set_text("Enter y")
                            text_input_z.set_text("Enter z")
                        elif (rect_y.collidepoint(event.pos)):
                            clearinput(1)
                            text_input_y.focus()
                            text_input_x.set_text("Enter x")
                            text_input_z.set_text("Enter z")
                        elif (rect_z.collidepoint(event.pos)):
                            clearinput(2)
                            text_input_z.focus()
                            text_input_x.set_text("Enter x")
                            text_input_y.set_text("Enter y")
                        else:
                            text_input_x.set_text("Enter x")
                            text_input_y.set_text("Enter y")
                            text_input_z.set_text("Enter z")
                            text_input_x.focus()
                    else:
                        zlock = True  # zlock on left click
                elif event.button == 3:  # teleport on right click
                    comunicate = False
                    blackcursor = False

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    zlock = False
                elif event.button == 3:
                    if (connectionstate == 1):
                        comunicate = True
                    blackcursor = True

            elif event.type == pygame.QUIT:
                run = False

            if (event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED or (not show_coordinates and state_for_inputs)):
                input_id = ""
                entered_text = ""
                try:
                    input_id = event.ui_object_id
                    entered_text = event.text
                except:
                    pass
                if (input_id == "x_entry"):
                    inserted_x = entered_text  # guardar valor tomado
                    active_input = 1
                    writing = True
                    text_input_x.disable()
                    text_input_y.focus()
                elif (input_id == "y_entry"):
                    inserted_y = entered_text  # guardar valor tomado
                    active_input = 2
                    writing = True
                    text_input_y.disable()
                    text_input_z.focus()
                elif (input_id == "z_entry" or not show_coordinates):
                    inserted_z = entered_text
                    active_input = 0
                    writing = True
                    text_input_z.disable()
                    if (show_coordinates):
                        time.sleep(0.3)
                    text_input_x.kill()
                    text_input_y.kill()
                    text_input_z.kill()
                    # ir a la posicion indicada
                    if (is_number(inserted_x)):
                        coord_x = float(inserted_x)
                    if (is_number(inserted_y)):
                        coord_y = float(inserted_y)
                    if (is_number(inserted_z)):
                        coord_z = float(inserted_z)
                    pygame.mouse.get_rel()
                    pygame.mouse.set_visible(False)
                    pygame.event.set_grab(True)
                    state2 = False
                    state_for_inputs = False
            manager.process_events(event)

    manager.update(UI_REFRESH_RATE)
    manager.draw_ui(screen)

    pygame.display.flip()
    time.sleep(0.003)

disconnect()
pygame.mouse.set_visible(True)
pygame.event.set_grab(False)
pygame.quit()
exit()


# arduino.read() != b'j'
