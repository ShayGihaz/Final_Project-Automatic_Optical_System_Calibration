'''
Written by Lev Galperin and Shay Gihaz
'''

# ------------------------------------------------------------------------------------------------------------------ #
#                            **This file is the main calibration process**
#           In this file we will consolidate the use of all parts of the system (camera, motors, osa),
#                                and perform automatic calibration of the system.
#         Important note: To calibrate the system, the user must calibrate the right part of the system
#   to a state where an image is obtained in the camera with the light beam coming out of the waveguide.

# IMPORTANT NOTE (!): If you wish to debug this code and see the images of the calibration process,
#                     search "IMAGE DEBUG" and remove the # from the code lines that framed by #---#.
#                     When image will be printed, to continue and close the image pres "0".
# ------------------------------------------------------------------------------------------------------------------ #

import Motor
import Camera
import OSA
import cv2
import os
import pythonnet
import clr
import time

from multiprocessing import Queue


# Set up the .NET runtime environment
pythonnet.load()
clr.AddReference("System")
from System import Decimal

flag_exposure = 0
osa = None
motorX = None
motorZ = None
motorY = None



def show_matrix(image):
    # for debug show matrix
    cv2.imshow('Grayscale Image', image)
    cv2.waitKey(0)  # Wait for any key press to close the window
    cv2.destroyAllWindows()  # Close all OpenCV windows


# --------------------------------------------get_image--------------------------------------------------------- #
# this function "read" the image, convert it to 2D numpy, and flatten the grayscale image to 1-dimensional array
# the input image is always in size 640x512.
# at the end, this function will delete the image and return the 1-dimensional array
# -------------------------------------------------------------------------------------------------------------- #
def get_image():                                          #the input image is 640x512
    image = cv2.imread('image0.bmp')                      #the output is 2D numpy --> (512, 640)
    # grayscale_image = cv2.imread('image0.bmp', cv2.IMREAD_GRAYSCALE) we can use only this and delete line 20
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Flatten the grayscale image to 1-dimensional array
    delete_image()

    # ------------------------------------------------------------------------ #
    # IMAGE DEBUG
    #show_matrix(gray_image)
    # ------------------------------------------------------------------------ #

    return gray_image



# ------------------------------------------object_is_center----------------------------------------------------- #
# This function, is designed to determine whether an object within an image is centered,
# by analyzing the distribution of pixels on either side of the object.
# The function can check for both horizontal and vertical centering based on a parameter.
#
# First, the function converts the input image into a binary image where the pixels are either black (0) or white (255).
# Next, it detects the contours in the binary image.
# Contours are simply the outlines or boundaries of objects within the image.
# Among all detected contours, the function finds the largest one, assuming it to be the object of interest.

#                       If column is set to True, it checks for vertical centering.
#                       If column is set to False, it checks for horizontal centering.
# the function counts the number of black pixels (zeros) from the top to the first white pixel and from the bottom to the first white pixel.
# These counts represent the number of black pixels on the left and right sides.
# After counting the pixels, the function calculates the difference between the counts on either side.
# If this difference is within a tolerance of 25 pixels, the object is considered centered.
# -------------------------------------------------------------------------------------------------------------- #
def object_is_center(image, countour,colum = False):
    # Apply binary thresholding - binary image where the pixels will be either 0 or 255 depend on thresh = 127
    ret, thresh = cv2.threshold(image, 70, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # find largest countur

    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    max_cnt = contours[0]
    height, width = thresh.shape
    left_side_zeros = 0
    right_side_zeros = 0

    x, y, w, h = cv2.boundingRect(max_cnt)

    if colum == True:
        middle_column = min(x + 5,640)
        column = thresh[:, middle_column]
        for pixel in column:
            if pixel == 0:
                left_side_zeros += 1 # this is the up sode
            else:
                break
        # Count zeros on the right side until hitting a non-zero pixel
        for pixel in reversed(column):
            if pixel == 0:
                right_side_zeros += 1 # this is the down side
            else:
                break
    else:
        #middle_row = height // 2         #get the line 512/2=256
        middle_row = min(y + 10,511)
        row = thresh[middle_row]
        # Count zeros on the left side until hitting a non-zero pixel
        for pixel in row:
            if pixel == 0:
                left_side_zeros += 1
            else:
                break
        # Count zeros on the right side until hitting a non-zero pixel
        for pixel in reversed(row):
            if pixel == 0:
                right_side_zeros += 1
            else:
                break
    # Calculate the difference between the left and right counts
    difference = left_side_zeros - right_side_zeros
    if abs(difference) <= 25:
        if(colum == True):
            print("The object is centered vertically.")
        else:
            print("The object is centered horizontally.")
        return True, difference, left_side_zeros, right_side_zeros
    return False, difference, left_side_zeros, right_side_zeros


def delete_image(file_name='image0.bmp'):
    if os.path.exists(file_name):
        # Delete the file
        os.remove(file_name)
        print(f"{file_name} has been deleted successfully.")
    else:
        print(f"The file {file_name} does not exist.")




# --------------------------------------------detect_state------------------------------------------------------ #
# this function processes an image to detect and classify an object as a "line" or "spot" based on its size.
# Additionally, it adjusts the camera's exposure settings based on this analysis.
#                                       first step: exposure-0.1
# If the width (w) of the object is greater than 110, it sets flag_exposure to 1 and the camera exposure to 0.01
# and return "line" for farther investigation of the image.
#                                       second step: exposure-0.01
# After we adjust the exposure to 0.01 if the width (w) of the object is greater than 45,
# it sets flag_exposure to 2, the camera exposure to 0.001 and return "spot".

# NOTE: if from some reason, some hardware will replace, it could lead to a situation were the width of the spot
#       will change.
#       In this situation, put a breakpoint in the lines: "if w > 110:" and "if w > 45:" and debug the system.
#       Also, an important variable that effect the width is the threshold!.
# -------------------------------------------------------------------------------------------------------------- #
def detect_state(image,camera):
    global flag_exposure

    #keep only pixels whiter than threshold
    ret, thresh = cv2.threshold(image, 70, 255, 0)

    # ------------------------------------------------------------------------ #
    # IMAGE DEBUG
    #show_matrix(thresh)
    # ------------------------------------------------------------------------ #

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    #find largest countur
    try:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        max_cnt = contours[0]

        # ------------------------------------------------------------------------ #
        # IMAGE DEBUG
        cv2.drawContours(image, [max_cnt], -1, (0, 0, 255), thickness=2) # Display the original image with the contour drawn
        #cv2.imshow('Image with Contour', image)
        #cv2.waitKey(0)  # Wait for any key press to close the window
        #cv2.destroyAllWindows()
        # ------------------------------------------------------------------------ #


    except:
        return "nothing",0,0


    x, y, w, h = cv2.boundingRect(max_cnt)


    if flag_exposure != 2:
        if flag_exposure != 1:
            #if w > 75:  # Check if it's a large width cuntur and make exposure smaller
            if w > 110: # from this width we think its spot and lower exposure - even with not optimal spot setting on right part of system
                flag_exposure = 1
                camera.set_new_exposure_param(0.01)
                return "line",max_cnt,w

            return "line", max_cnt,w

        else:
            if w > 45:# from this width we think its spot and continue to OSA analyze - even with not optimal spot setting on right part of system
                flag_exposure = 2
                camera.set_new_exposure_param(0.001)
                return "line", max_cnt, w

            else:
                #pop-up
                print("user: we think we have some spot detected but its bad, please calibbrate better right side of system")
                return "bad_spot", max_cnt, w           # while returning "bad_spot" we do a pop-up


    else:
        return "spot", max_cnt,w



def process_line(motorX,motorY,motorZ,y_cord):
    motorY.move_exactly(y_cord)



# --------------------------------------process_end_line_condition---------------------------------------------- #
# This function is to produce a condition for the end of the light beam.
‫#‬ When we perform the search algorithm for the "spot" in the laser beam displayed on the camera, 
‫#‬ there is a situation where we look for the spot and go down or up the laser beam when the location we are looking for 
‫#‬ is in the other direction, so if we reach a situation where we have reached the end of the beam 
‫#‬ so that the resulting light beam is a quarter From the size of the camera screen, 
‫#‬ we will conclude that this is not the right direction, so stop searching in this direction and move to the other direction.
‫#‬
# -------------------------------------------------------------------------------------------------------------- #
def process_end_line_condition(image,direction):
    ret, thresh = cv2.threshold(image, 70, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if direction == 'up':
        try:
            contours = sorted(contours, key=lambda cnt: cv2.boundingRect(cnt)[1])
            highest_cnt = contours[0]

            # ------------------------------------------------------------------------ #
            # IMAGE DEBUG
            cv2.drawContours(image, [highest_cnt], -1, (0, 0, 255), thickness=10)  # Display the original image with the contour drawn
            #cv2.imshow('Image with Contour', thresh)
            #cv2.waitKey(0)  # Wait for any key press to close the window
            #cv2.destroyAllWindows()
            # ------------------------------------------------------------------------ #

            x, y, w, h = cv2.boundingRect(highest_cnt)
            if (y < 384):
                return True
            return False
        except:
            pass
    else:
        try:
            contours = sorted(contours, key=lambda cnt: cv2.boundingRect(cnt)[1], reverse=True)
            highest_cnt = contours[0]
            x, y, w, h = cv2.boundingRect(highest_cnt)
            if (y+h > 128):
                return True
            return False
        except:
            pass

    return True



# --------------------------------------------process_spot------------------------------------------------------ #
# This function adjust the position of a specific motor and analyze the resulting power output from the OSA
# to find the optimal position.
# First, it calculates a new position for the motor by adding a specific increment to the current position.
# This increment is determined by multiplying the step value by the count and adding it to current position (pos).
# The motor then moves to this position using the move_exactly method.
#   step - define how much the motor will moved in each step (hard calibration - 0.01, soft calibration - 0.001).
#   count - counts how much steps we already moved.
#
# Next, the function take the average power at this new position by calling the getAnalysis method from the OSA.
# The res parameter indicates whether the function is in the first loop with a hard calibration
# or a subsequent loop with a soft calibration.
#
# At the end, the function return the average power.
# -------------------------------------------------------------------------------------------------------------- #
def process_spot(step,motor,pos,count,res):
    motor.move_exactly((pos + Decimal(count*step)))
    average_power = osa.getAnalysis(res) #if res =1 it means first loop with hard calibration else soft calibration
    # if(average_power>best_average_power):
    #     best_average_power = average_power
    #     best_pos = pos+count
    # #motor.move(best_pos)   #move to best position
    return average_power



# ------------------------------------------find_optimal_position------------------------------------------------ #
# This function find the optimal motors positions such that we will get the highest average power from the OSA.
# first, we enter a while loop that continues as long as spot_count is less than or equal to the absolute value of stop
# by using process_spot function we move the motor and measure the average power of all positions of the axes.
#
# after we determined what is the best position in the specific axes, the function will move the motor to this position.
#
# this function iterate X and Y axis 3 times to find the best position on the camera,
# only after that we will find the best motor position of Z (because this axes is control of the focus of the camera).
# -------------------------------------------------------------------------------------------------------------- #
def find_optimal_position(step, motor, flag, spot_count,axis_counter,res):
    pos = motor.coordinate
    best_pos = pos
    best_average_power = -100
    #step = 0.01

    stop = abs(spot_count)
    # Find the best position
    while spot_count <= stop:
        average_power = process_spot(step, motor, pos,spot_count,res)
        if average_power > best_average_power:
            best_average_power = average_power

            best_pos = pos + Decimal(spot_count*step)

        spot_count += 1

        
        # we need to add counter that indicate how match operation we are doing on the axes
        # if the counter is 6 this is means that we did 3 operation on x and 3 operations on y
        # then we will decrease the step size to be able to add more resolution to the system


    if spot_count > stop:
        spot_count = stop
        motor.move_exactly(best_pos)  # Move to the best position
        print("best power: ",best_average_power)

        if flag == 'x':
            flag = 'y'
            return flag,best_average_power,best_pos    # Move to the next axis
        if flag == 'y':
            if axis_counter <4:
                flag = 'x'
                return flag,best_average_power,best_pos
            flag = 'z'
            return flag,best_average_power,best_pos
                # Move to the next axis
        else:
            print("Optimal coordinates for x, y and z have been found")
            return flag, best_average_power, best_pos
    # # else:
    #     print("Optimal coordinates for x and y have been found")
    #     flag = 'z'
    #     return flag  # Terminate the loop



# ------------------------------------------object_to_center---------------------------------------------------- #
# this function is designed to reposition an object to the center of an image by moving a motor.
# The movement is calculated by the difference in the number of black pixels on the left and right sides of the object,
# and adjusts for both horizontal and vertical centering, depending on the column parameter.
#
# this function gets the parameters from the function "object_is_center".
#
# our image is in size 640x512, so first if the need to horizontal centering, column = True
# other ways column = False, and we are on the state of vertical centering.
# second, by using "difference" parameters the function could know if the object is more to the left/right/up/down side.
# column = False , difference > 1 -----> right side
# column = False , difference < 0 -----> lest side
# column = True , difference > 1 -----> down side
# column = True , difference < 0 -----> up side
#
# If function is in vertical centering, the number of steps the motor needs to move is (num_zeros_to_move / 24),
# since 512 pixels correspond to 21 steps (step = 0.01), and 512/21 is approximately 24.
# If function is in horizontal centering, the number of steps the motor needs to move is (num_zeros_to_move / 20),
# since 640 pixels correspond to 31 steps (step = 0.01), and 640/31 is approximately 20.
# -------------------------------------------------------------------------------------------------------------- #
def object_to_center(difference, left_side_zeros, right_side_zeros, column = False):
    sum_zeros = (left_side_zeros + right_side_zeros) // 2
    if difference > 1:  #the object is on the right side
        num_zeros_to_move = sum_zeros - right_side_zeros
        if column == True:
            num_step_to_move = (num_zeros_to_move / 24) * 0.01  # 512 pixels, if step is 0.01 the from right side to left side is 21 step, 512/21=24.3
            motorY.move(-num_step_to_move)
        else:
            num_step_to_move = (num_zeros_to_move / 20) * 0.01  # 640 pixels, if step is 0.01 the from right side to left side is 31 step, 640/31=20.6
            motorX.move(num_step_to_move)
    else:  #the object is on the left side
        num_zeros_to_move = sum_zeros - left_side_zeros
        if column == True:
            num_step_to_move = (num_zeros_to_move / 24) * 0.01  # 512 pixels, if step is 0.01 the from right side to left side is 21 step, 512/21=24.3
            motorY.move(num_step_to_move)
        else:
            num_step_to_move = (num_zeros_to_move / 20) * 0.01  # 640 pixels, if step is 0.01 the from right side to left side is 31 step, 640/31=20.6
            motorX.move(-num_step_to_move)



# ---------------------------------------------start_CAl_main--------------------------------------------------- #
#                               THIS IS THE MAIN FUNCTION WHO DOES IT ALL (!).
# To explain this function we will divide the code lines into parts.
# PART 1: First, in this part we will connect all the hardware to our code, the motors, camera and OSA.
#         Second, we will start a "while True" loop that ends only when we finish the whole calibration process.
#         this loop start with captured an image from the camera, define step=0.01, and call the "detect_state" function
#         We always stay within this loop!

# PART 2: If we received that the state is "nothing", then the user most try again to give us the initial state
#         that we demand for the calibration process.
#         The initial state is where the camera gets a nice line of the light that comes out from the waveguide.

# PART 3: We received that the state is "line", then first we will see if the line is centered,
#         if not we will center the line, and now we can be sure that by searching the spot, the object will not go
#         out from the image boundaries.
#   PART 3.1: After we centered the line object, we want to search for the "spot"
#             This "spot" is the specific position that the light comes out from the waveguide.
#             To do that, we will move the "line" up and down using the motors, and try to reach the spot
#             we will move 120 times up and 120 times down in the process of finding the "spot" object.
#             In the function 'detect_state' we search for the specific conditions that define a "spot" object,
#             and also decrease the exposure of the camera.

# PART 4:
#   PART 4.1: We received that the state is "spot", then first we will see if the spot is centered,
#             if not we will center the line horizontally and vertically.
#   PART 4.2: Now we can start the calibration process with thw OSA.
#             In this part we will search the optimal position in "hard calibration" way, means that we will search
#             this position in the entire image (640x512) with step=0.01, and define the resolution of the OSA to HIGH1.
#             This loop will end when we are finished work 3 times on X,Y axis and one time on Z axes.
#   PART 4.3: After we find the best position in the "hard calibration", the next step is "soft calibration".
#             In this part we will search the optimal position with step=0.001 on a very small area (20x24),
#             and define the resolution of the OSA to HIGH2.
#             This loop will end when we are finished work 2 times on X,Y axis and one time on Z axes.
#
#             AFTER WE FINISHED WORK ON Z AXES IN THE SECOND LOOP, THE SYSTEM IS CALIBRATED !
# -------------------------------------------------------------------------------------------------------------- #
def start_CAl_main(output_queue):
    #def start_CAl_main():
        # Init
        global  osa,motorX, motorZ, motorY, camera

	# ----------------------------- PART 1 ----------------------------- #
        osa = OSA.OSA('10.0.0.101')
        output_queue.put("Connected to OSA\n")

        motorX = Motor.Motor("27257412")
        output_queue.put("Connected to motorX: SN 27257412\n")
        motorZ = Motor.Motor("27257467")
        output_queue.put("Connected to motorZ: SN 27257467\n")
        motorY = Motor.Motor("27257430")
        output_queue.put("Connected to motorY: SN 27257430\n")
        camera = Camera.Camera()
        up_line_count = 0
        down_line_count = 0
        init_coordiante = motorY.coordinate
        spot_count = -15
        best_w_down = 0
        best_w_up = 0
        best_line_position_up = 0
        best_line_position_down = 0
        flag_state = False

        while True:
            delete_image()
            camera.save_image()
            image = get_image()
            #for debug print the image matriz to see if its the sie like the saved image
            state = detect_state(image,camera)
            if state[0] == "line" and not(flag_state):
                flag_state = True
                output_queue.put("Detected state: Line\n")
                output_queue.put("Searching for a light spot...\n")


            step = Decimal(0.01)

            flag = 'x'

	     	
            if state[0] == 'bad_spot':
                # change the exposer and gain of the camera to see if its changes the state.
                output_queue.put("TERMINATE_bad_Spot")
                print("detected bad spot")
                exit(0)


	     # ----------------------------- PART 2 ----------------------------- #
            if state[0] == 'nothing':
                # change the exposer and gain of the camera to see if its changes the state.
                output_queue.put("TERMINATE_nothing")
                print("couldn't detect even a line")
                exit(0)

	     # ----------------------------- PART 3 ----------------------------- #
            if state[0] == 'line':
                flag_is_center, difference, left_side_zeros, right_side_zeros = object_is_center(image,state[1])
                while not flag_is_center:
                    object_to_center(difference, left_side_zeros, right_side_zeros)
                    camera.save_image()
                    image = get_image()
                    flag_is_center, difference, left_side_zeros, right_side_zeros = object_is_center(image,state[1])
                # this function need receive how match zeros are in the left and right side of the object
                # from line (512/2=256) if the numpy matrix.
                # then move the motors so the zeros from the sides of the object will be equal.
                # after we're doing this we can be sure that by searching the spot, the object will not go
                # out from the image boundaries.

                # ----------------------------- PART 3.1 ----------------------------- #
                if (up_line_count < 120):
                    if process_end_line_condition(image,"up"):
                        temp_Y_coordinate = init_coordiante + step if up_line_count == 0 else temp_Y_coordinate + step
                        up_line_count += 1
                        process_line(motorX, motorY, motorZ, temp_Y_coordinate)

                        #check for best w over all up iterations
                        if state[2] > best_w_up:
                            best_w_up = state[2]
                            best_line_position_up = init_coordiante + ((Decimal(up_line_count-4))*step)

                    else:
                        up_line_count = 120
                        temp_Y_coordinate = init_coordiante
                        process_line(motorX, motorY, motorZ, temp_Y_coordinate)

                else:
                    if process_end_line_condition(image, "down"):
                        if (down_line_count < 120):
                            temp_Y_coordinate = init_coordiante-step if down_line_count == 0 else temp_Y_coordinate-step
                            down_line_count += 1
                            process_line(motorX, motorY, motorZ, temp_Y_coordinate)

                            # check for best w over all down line iterations
                            if state[2] > best_w_down:
                                best_w_down = state[2]
                                best_line_position_down = init_coordiante - (Decimal(down_line_count+4)*step)



                        else:
                            output_queue.put("TERMINATE_spot")

                            #move motor to best width in line iterations- probably the spot will be there after user calibrate right side of system
                            if best_w_down>best_w_up:
                                motorY.move_exactly(best_line_position_down)
                            else:
                                motorY.move_exactly(best_line_position_up)

                            print("couldn't detect spot - only line")
                            # there is an option that in the image we will get 2 lines.
                            # sometimes the chip has a deflaction causes the continuous line to split
                            exit(0)
	     # ----------------------------- PART 4 ----------------------------- #
            else:
                # now first we have the spot in our image
                # so first of all we need to center the spot and make the line disappear
                # change the exposer of the camera
                # now we need to take the spot to the center
                # all the pixels should be black -->0, only the spot pixels are white -->1
		 # ----------------------------- PART 4.1 ----------------------------- #
                output_queue.put("Detected state: Spot\n")
                flag_is_center, difference, left_side_zeros, right_side_zeros = object_is_center(image,state[1])
                while not flag_is_center:
                    object_to_center(difference, left_side_zeros, right_side_zeros)
                    camera.save_image()
                    new_image = get_image()
                    flag_is_center, difference, left_side_zeros, right_side_zeros = object_is_center(new_image,state[1])

                flag_is_center, diff, up_side_zeros, down_side_zeros = object_is_center(image,state[1], colum=True)
                while not flag_is_center:
                    object_to_center(diff, up_side_zeros, down_side_zeros, column=True)
                    camera.save_image()
                    new_image = get_image()
                    flag_is_center, diff, up_side_zeros, down_side_zeros = object_is_center(new_image,state[1], colum=True)
                axis_counter =0
                best_power_y = -210
                best_power_z = -210
		 # ----------------------------- PART 4.2 ----------------------------- #
                #first loop for hard calibration - big step and limits to search,resolution of HIGH1
                output_queue.put("Starting first calibration loop with OSA\n")
                while True:
                    if flag == 'x':
                        axis_counter+=1
                        flag,best_power_x,best_pos_x = find_optimal_position( 0.01,motorX, flag, -15,axis_counter,1)
                        #camera.save_image()
                        #new_image = get_image()



                    elif flag == 'y':
                        flag,best_power_y,best_pos_y = find_optimal_position(0.01,motorY, flag, -10,axis_counter,1)
                        #camera.save_image()
                        #new_image = get_image()



                    elif flag == 'z':
                        flag,best_power_z,best_pos_z = find_optimal_position(0.01,motorZ, flag, -3,axis_counter,1)
                        #camera.save_image()
                        #new_image = get_image()

                        output_queue.put("Finished first loop of motor movements - HIGH1 resolution in OSA and large motor steps, Starting second loop\n")
                        message = f"Highest power found in first loop is: {best_power_z}\n"
                        output_queue.put(message)
                        print("finished first loop")
                        flag = 'x'
                        break
		 
		 # ----------------------------- PART 4.3 ----------------------------- #
                #second loop for soft calibration - small step and limits to search,resolution of HIGH2
                axis_counter = 1
                while True:
                    if flag == 'x':
                        axis_counter+=1
                        flag,best_power,best_pos_x = find_optimal_position( 0.001,motorX, flag, -10,axis_counter,2)
                        camera.save_image()
                        new_image = get_image()
                    elif flag == 'y':
                        flag,best_power,best_pos_y = find_optimal_position(0.001,motorY, flag, -10,axis_counter,2)
                        camera.save_image()
                        new_image = get_image()
                    elif flag == 'z':
                        flag,best_power,best_pos_z = find_optimal_position(0.001,motorZ, flag, -3,axis_counter,2)
                        camera.save_image()
                        new_image = get_image()
                        output_queue.put("Finished second loop of motor movements - HIGH2 resolution in OSA and small motor steps\n")
                        message = f"Highest power found in second loop is: {best_power_z}\n"
                        output_queue.put(message)
                        print("finished second loop")
                        exit(0)




if __name__ == "__main__":
    start_CAl_main()
