import cv2
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import openpyxl

#Get pixel/distance (using ImageJ software) to output actual diameters of circles
global result, img, table_data, up_img, pixel_distance, detected_circles

dp = 1
accum_ratio = 1
min_dist = 5
p1 = 40
p2 = 30
minDiam = 1
maxDiam = 30
scalebar = 10
min_range = 0
max_range = 100
intervals = 10
rad_list =[]
detected_circles = []

def clear_plt():
    plt.clf()

def autoDetect(up_img, accum_ratio, min_dist, p1, p2, minDiam, maxDiam, pixel_distance):
    global result, img, table_data, rad_list, detected_circles

    # Read image.
    img = cv2.imread(up_img, cv2.IMREAD_COLOR)

    # Convert to grayscale.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur using 3 * 3 kernel.
    gray_blurred = cv2.blur(gray, (5, 5))



    # Apply Hough transform on the blurred image.
    detected_circles = cv2.HoughCircles(gray_blurred, 
                    cv2.HOUGH_GRADIENT, dp = int(accum_ratio), minDist = int(min_dist*pixel_distance), 
                    param1 = int(p1), param2 = int(p2), minRadius = int(minDiam*pixel_distance/2), maxRadius = int(maxDiam*pixel_distance/2))



def autoDetectBin(up_img, threshold,accum_ratio, min_dist, p1, p2, minDiam, maxDiam, pixel_distance):
    global result, img, table_data, rad_list, detected_circles

    img = cv2.imread(up_img, cv2.IMREAD_COLOR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thres,binImg = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
    # Blur using 3 * 3 kernel.
    blurred = cv2.blur(binImg, (5, 5))



    # Apply Hough transform on the blurred image.
    detected_circles = cv2.HoughCircles(blurred, 
                    cv2.HOUGH_GRADIENT, dp = int(accum_ratio), minDist = int(min_dist*pixel_distance), 
                    param1 = int(p1), param2 = int(p2), minRadius = int(minDiam*pixel_distance/2), maxRadius = int(maxDiam*pixel_distance/2))


def processCircles(up_img, pixel_distance, manual_list):
    global detected_circles, rad_list, result, img, bottom_10percentile, top_90percentile
    # Draw circles that are detected.
    rad_list=[]
    img = cv2.imread(up_img, cv2.IMREAD_COLOR)
    result = ''
    try:
        if (detected_circles is None) and (len(manual_list) == 1):
            return 'No circles found!\n'

        elif len(manual_list) >1:
            manual_list.sort()
            bottom_10percentile = int(len(manual_list)*0.1)
            top_90percentile = int(len(manual_list)*0.9)
            result += '# of circles found: ' + str(len(manual_list))
            rad_list = manual_list

        else:
            
            # Convert the circle parameters a, b and r to integers.
            detected_circles = np.uint16(np.around(detected_circles))
            
            for pt in detected_circles[0, :]:
                a, b, r = pt[0], pt[1], pt[2]

                # Draw the circumference of the circle.
                cv2.circle(img, (a, b), r, (0, 255, 0), 2)

                # Draw a small circle (of radius 1) to show the center.
                cv2.circle(img, (a, b), 1, (0, 0, 255), 3)
                
            
            new_name = up_img[:-4] + '_detected' + up_img[-4:]
            cv2.imwrite(new_name,img)

            #Loop to convert radius (pixel) values to diameter
            for x in range(detected_circles.shape[1]):
                diam = detected_circles[0,x,2]*2/pixel_distance    
                rad_list.append(round(diam,1))

            rad_list.sort()

            bottom_10percentile = int(len(rad_list)*0.1)
            top_90percentile = int(len(rad_list)*0.9)

            result += '# of circles found: ' + str(detected_circles.shape[1]) 

        result +='\nAvg diam. = ' + "%.1f"%np.average(rad_list) + 'um' 
        result +='\nD10 = '+ str(rad_list[bottom_10percentile])+'um'+'\nD50 = ' + "%.1f"%np.median(rad_list) + "um" 
        result +='\nD90 = '+ str(rad_list[top_90percentile])+'um'
    except IndexError:
        pass
    return result

def tableData():
    global rad_list, row_list, dataForTable, col_list, bottom_10percentile, top_90percentile, detected_circles
    dataForTable = {}
    col_list = []
    row_list = []
    Diam_um = 'Diameter(um)'

    if len(rad_list)>0:
        for items in range(len(rad_list)):
            col_list.append(dict(Diam_um = rad_list[items]))

        for rows in range(len(rad_list)):
            row_list.append('rec'+ str(rows+1))
        
        dataForTable = dict(zip(row_list,col_list))

        try:    
            temp_one = dataForTable['rec1']['Diam_um']
            temp_two = dataForTable['rec2']['Diam_um']
            temp_three = dataForTable['rec3']['Diam_um']
            temp_four = dataForTable['rec4']['Diam_um']
            temp_five = dataForTable['rec5']['Diam_um']

            dataForTable.update({'rec1':{'Diam_um': str(temp_one) , 'Col2': '# of Circles', 'Col3': str(len(rad_list))},
            'rec2':{'Diam_um': str(temp_two),'Col2': 'Avg Diam.(um)', 'Col3': "%.1f"%np.average(rad_list)}, 
            'rec3':{'Diam_um': str(temp_three) ,'Col2': 'D10 (um)', 'Col3': str(rad_list[bottom_10percentile])},
            'rec4':{'Diam_um': str(temp_four),'Col2': 'D50 (um)', 'Col3': "%.1f"%np.median(rad_list)},
            'rec5':{'Diam_um': str(temp_five) ,'Col2': 'D90 (um)', 'Col3': str(rad_list[top_90percentile])}
            })

        except KeyError:
            pass
    return dataForTable


def histoPlot(up_img, min_range, max_range, intervals):
    global rad_list
    #Plot histogram
    plt.xlabel('Diameter (um)')
    plt.ylabel('Frequency')
    plt.title('Particle Size Distribution')
    (n, bins, patch) = plt.hist([rad_list], bins=np.arange(min_range,max_range+1,intervals), rwidth=0.9)
    plt.xticks(np.arange(min_range,max_range,intervals))
  #  plt.gca().grid(which='major', axis='y')
    plt.savefig((up_img[:-4] + '_histogram.png'), dpi = 500)
    plt.clf()
    


   # pd.DataFrame(rad_list).to_excel('emulsions_D50_list_1.xlsx',header=False, index=False)
    
    