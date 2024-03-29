import csv
import cv2
import datetime
import math

#Кординати датчиків
map = [[3.3, 0], [0.3, 0], [0.23, 21], [3.47, 20.8], [0.67, 7.8], [2.96, 12]]

file_url = 'data/data-1-1.csv'
map_bg = 'res/map.png'
line_th = 1
max_x = 4.6
max_y = 21
filter_d = 10
debug = False


map_img = cv2.imread(map_bg)

def show(img):
    cv2.imshow("dev", img)
    cv2.waitKey(-1)

def transform_cords(arr, img):
    x = max_y - arr[1]
    x = x / max_y * img.shape[1]
    y = arr[0]
    y = y / max_x * img.shape[0]
    return round(x), round(y)

def add_tracks(map, track):
    for i in range(1, len(track)):
        x1, y1 = transform_cords(track[i-1], map)
        x2, y2 = transform_cords(track[i], map)
        cv2.line(map, (x1, y1), (x2, y2), (0, 0, 255 - 150 * i / len(track)), line_th)

def optimize_cords_for_text(img, x, y):
    if x - 20 < 0:
        x += 10
    else:
        if x + 40 > img.shape[1]:
            x -= 50
        else:
            x -= 10
    if y - 20 < 0:
        y += 15
    else:
        if y + 20 > img.shape[0]:
            y -= 15
        else:
            y -= 5
    return x, y

def add_points(map, track):
    for i in range(len(track)):
       x, y = transform_cords(track[i], map)
       cv2.circle(map, (x, y), line_th * 3, (0, 0, 255), -1)
       x, y = optimize_cords_for_text(map,x, y)
       cv2.putText(map, str(i) + '. ' + track[i][2]+ ' ' + track[i][3], (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (200, 0, 200), 1, cv2.LINE_AA)

def generate_track_map(track):
    map = map_img.copy()
    add_tracks(map, track)
    add_points(map, track)
    return map;

def min_f(a, b):
    if a > b:
        return b
    else:
        return a

def max_f(a, b):
    if a < b:
        return b
    else:
        return a

def delz(arr):
    buf = []
    for e in arr:
        if e[1] == 0:
            buf.append(e)
    for e in buf:
        arr.remove(e)
    return arr

def average(arr):
    s = 0;
    for e in arr:
        s += e
    return s / len(arr)

def optimize(arr):
    adr = -1
    for i in range(len(arr)):
        adr = -1
        buf = []
        for j in range(len(arr)):
            if arr[j][0] == i + 1:
                if adr == -1:
                    adr = j;
                buf.append(arr[j][1])
                arr[j][1] = 0
        if adr != -1:
            arr[adr][1] = average(buf)
    delz(arr)
    return arr

def sort(arr):
    return sorted(arr, key = lambda e: -e[1])


def cord(arr, i = 2):
    x = 0.
    y = 0.
    r = 0.
    for j in range(i):
        x1, y1 = map[int(arr[j][0]) - 1]
        rl = db_to_n(arr[j][1])
        r += rl
        x += x1 * rl
        y += y1 * rl
    return [x/r, y/r]


def filter(arr):
    et = arr[0][1]
    buf = []
    for i in range(1, len(arr)):
        if et - arr[i][1] > filter_d :
            buf.append(arr[i])
    for e in buf:
        arr.remove(e)
    return arr

def db_to_n(x):
    return math.pow(10, (float(x))/10)

def timestamp_to_datetime(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S.%f")

def getZone(y):
    if y < 7.8:
        return 'C3'
    if y < 12:
        return 'C2'
    return 'C1'

def timeFilter(track):
    zone = ''
    total_zone = ''
    time_in_zone = 0
    for i in range(len(track)):
        if(total_zone != track[i][2]):
            total_zone = track[i][2]
            time_in_zone = track[i][4]
        else:
            if (track[i][4] - time_in_zone)/1000000 >= 5:
                zone = total_zone
        track[i][2] = zone
    return track

def removeRepeats(arr):
    zone = arr[0][2]
    base = arr[0][3]
    buf = []
    for i in range(len(arr)):
        z = arr[i][2]
        b = arr[i][3]
        if (zone == z and base == b) or z == '':
            buf.append(arr[i])
        else:
            zone = z
            base = b
    for e in buf:
        arr.remove(e)
    return track

def getTrack(data):
    i = 0
    buf = []
    track = []
    for row in data:
        i += 1
        buf.append([int(row['eddystone_instance_id']), float(row['rssi'])])
        if i == 6 or (i > 3 and row == data[len(data) - 1]):
            i = 0
            buf = optimize(buf)
            if len(buf) < 3 or buf[0][1] - buf[len(buf) - 1][1] < 15:
                buf = []
                continue
            buf = sort(buf)
            buf = filter(buf)
            x, y = cord(buf, len(buf))
            base = ''
            if len(buf) == 1 or buf[0][1] - buf[1][1] > 3:
                base = 'B' + str(buf[0][0])
            track.append([x, y, getZone(y), base, int(timestamp_to_datetime(row['timestamp']).strftime("%Y%m%d%H%M%S%f"))])
            buf = []
    return track

with open(file_url, newline='') as File:
    reader = csv.DictReader(File)
    rows = []
    for row in reader:
        rows.append(row)
    sorted(rows, key=lambda row: int(timestamp_to_datetime(row['timestamp']).strftime("%Y%m%d%H%M%S%f")))
    track = getTrack(rows)
    track = timeFilter(track)
    if len(track) > 0:
        track = removeRepeats(track)
        m = generate_track_map(track)
        cv2.imwrite(file_url[:-3] + "jpg", m)
        my_file = open(file_url[:-3] + "txt", "w")
        for e in track:
            my_file.write(e[2] + ' ' + e[3] + '\n')
        my_file.close()
        if debug:
            print(track)
            show(m)




