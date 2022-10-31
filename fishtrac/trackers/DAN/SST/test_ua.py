from tracker import SSTTracker, TrackerConfig, Track
import cv2
from data.ua_detection_data_reader import UADetectionDataReader
import numpy as np
from config.config import config
from utils.timer import Timer
import argparse
import os
import sys

parser = argparse.ArgumentParser(description='Single Shot Tracker Test')
parser.add_argument('--version', default='v1', help='current version')
parser.add_argument('--ua_image_root', default=config['ua_image_root'], help='Image Root')
parser.add_argument('--ua_detection_root', default=config['ua_detection_root'], help='Detection Root')
parser.add_argument('--ua_ignore_root', default=config['ua_ignore_root'], help='Ignore folder Root')
parser.add_argument('--save_folder', default=config['save_folder'], help='save file folder Root')
parser.add_argument('--show_image', default=False, help='show image if true, or hidden')
parser.add_argument('--save_video', default=False, help='save video if true')
parser.add_argument('--use_ignore', default=True, help='use ignore or not')
parser.add_argument('--detection_threshold', default=0.3, help='the threshold of detection')



    
def test(choice=None, sequence_list=None, img_root=None):
    if img_root is None:
        image_root = args.ua_image_root
    detection_root = args.ua_detection_root
    ignore_root = args.ua_ignore_root

    if not os.path.exists(image_root) or not os.path.exists(detection_root) or not os.path.exists(ignore_root):
        raise FileNotFoundError('Pls check the file of parameters')

    print('''
    ==============================
    =     Start Reading Files    =
    ==============================
    ''')

    #if not sequence_list is None:
    #    sequences = np.loadtxt(sequence_list, dtype='str')
    #else:
    #    sequences = os.listdir(image_root)
    sequences = os.listdir(image_root)

    sequences_basename = [os.path.basename(s) for s in sequences]
    # print(sequences_basename)
    # validation
    for seq in sequences:
        if not os.path.exists(os.path.join(image_root, seq)):
            raise FileNotFoundError()

    all_image_folders = sorted(
        [os.path.join(image_root, d) for d in sequences]
    )
    print(sequences_basename)

    all_detection_files = [os.path.join(detection_root, f+'_Det_'+config['detector_name']+'.txt') for f in sequences_basename]
    all_ignore_files = [os.path.join(ignore_root, f+'_IgR.txt') for f in sequences_basename]
    # all_detection_files = sorted(
    #     [os.path.join(detection_root, f) for f in os.listdir(detection_root) if 'MVI_' in f and os.path.basename(f) in sequences_basename]
    # )
    # all_ignore_files = sorted(
    #     [os.path.join(ignore_root, f) for f in os.listdir(ignore_root) if os.path.basename(f)[:-8] in sequences_basename]
    # )
    # print(all_ignore_files)

    ignore_file_base_name = [os.path.basename(f)[:-8] for f in all_ignore_files]
    detection_file_base_name = [os.path.basename(f)[:9] for f in all_detection_files]
    
    save_folder = args.save_folder
    choice_str = ''
    if not choice is None:
        choice_str =  TrackerConfig.get_configure_str(choice)
        TrackerConfig.set_configure(c)
        save_folder = os.path.join(args.save_folder, choice_str)
        

    print(all_image_folders)

    for image_folder in all_image_folders:
        image_folder_base_name = os.path.basename(image_folder)
        i = ignore_file_base_name.index(image_folder_base_name)
        ignore_file = all_ignore_files[i]
        image_folder_base_name = os.path.basename(image_folder)
        i = ignore_file_base_name.index(image_folder_base_name)
        ignore_file = all_ignore_files[i]

        print(image_folder_base_name)
        print(detection_file_base_name)
        j = detection_file_base_name.index(image_folder_base_name)
        detection_file = all_detection_files[j]
        run_DAN_once(image_folder, ignore_file, detection_file, image_folder_base_name, save_folder, args.save_video, args.show_image, args.detection_threshold)
    # print(timer.total_time)
    # print(timer.average_time)

def run_DAN_once(image_folder, ignore_file, detection_file, base_name, save_folder, save_video=False, show_image=False, detection_threshold=0):

     
    video_title = os.path.split(os.path.dirname(image_folder))[1]
    object_class = "fish"
    if video_title[:3] == "MVI":
        object_class = "car"
    if video_title[:5] == "MOT17":
        object_class = "ped"
    print("SEQUENCE_TITLE: {}".format(video_title))
    print("OBJECT_CLASS: {}".format(object_class))

    #select model based on object class
    import pathlib
    curPath = str(pathlib.Path(__file__).parent.absolute())
    config['resume'] = curPath + '/weights/ped-fish-664e-120i-last-it.pth' #ped+fish
    if object_class == "car" or object_class == "ped":
        config['resume'] = curPath+ '/weights/ped-car-664e-120i-last-it.pth' #ped+car

    print("RESUME PATH: {}".format(config['resume']))

    saved_file_name_format = os.path.join(save_folder, '{}.txt')
    saved_video_name_format = os.path.join(save_folder, '{}.avi')
    
    saved_file_name = saved_file_name_format.format(base_name)
    saved_video_name = saved_video_name_format.format(base_name)
    vw = None
    print(ignore_file)
    print(image_folder)
    print(detection_file)
    if not os.path.exists(image_folder):
        print("error: image directory does not exist! ", image_folder)
        return
    if not os.path.exists(detection_file):
        print("error: detection file does not exist! ", detection_file)
        return
    if ignore_file is not None and not os.path.exists(ignore_file):
        print("error: ignore file isn't none, but doiesn't exist", ignore_file)
        return
    if not os.path.exists(save_folder):
         os.mkdir(save_folder)
    print('processing ', image_folder, '>>>>>>>>>>>>>>>>>>')

    tracker = SSTTracker()
    reader = UADetectionDataReader(image_folder, detection_file, ignore_file, 0.0)
    #0.0 is the detection thresh, filtered upstream
    result = list()
    result_str = saved_file_name
    timer = Timer()
    for i, item in enumerate(reader):
        if item is None:
            continue

        img = item[0]
        det = item[1]

        if img is None or det is None or len(det) == 0:
            continue

        if len(det) > config['max_object']:
            det = det[:config['max_object'], :]

        h, w, _ = img.shape
        if vw is None and save_video:
            vw = cv2.VideoWriter(saved_video_name, cv2.VideoWriter_fourcc('M','J','P','G'), 10, (w, h))

        det[:, [2, 4]] /= float(w)
        det[:, [3, 5]] /= float(h)

        timer.tic()
        image_org = tracker.update(img, det[:, 2:6], show_image, i)
        timer.toc()
        if i % 20 == 0:
            print('{}:{}, {}\r'.format(saved_file_name, i, int(i * 100 / reader.length)))

        if show_image and not image_org is None:
            cv2.imshow('res', image_org)
            cv2.waitKey(1)

        if save_video and not image_org is None:
            vw.write(image_org)

        for t in tracker.tracks:
            n = t.nodes[-1]
            if t.age == 1:
                b = n.get_box(tracker.frame_index-1, tracker.recorder)
                result.append(
                    [i+1] + [t.id+1] + [b[0]*w, b[1]*h, b[2]*w, b[3]*h] + [-1, -1, -1, -1]
                )
    # save data
    if len(result) > 0 :
        save_format = '%d %d %1.2f %1.2f %1.2f %1.2f %d %d %d %d'
    else:
        save_format = '%i'
    np.savetxt(saved_file_name, np.array(result).astype(int), fmt=save_format)
    np.savetxt(os.path.splitext(saved_file_name)[0]+'-speed.txt', np.array([timer.total_time]), fmt='%.3f')
    print(result_str)

if __name__ == '__main__':
    args = parser.parse_args()
    c = TrackerConfig.get_ua_choice()
    #threshold = [i*0.1 for i in range(0,10)]

    threshold = [0.5]
    save_folder = args.save_folder
    if not os.path.exists(args.save_folder):
        os.mkdir(args.save_folder)
    for t in threshold:
        args.detection_threshold = t
        args.save_folder = os.path.join(save_folder, '{0:0.1f}'.format(t))
        if not os.path.exists(args.save_folder):
            os.mkdir(args.save_folder)
        test(c, './config/ua_experienced.txt')
        print('Finished threshold:', t)
    print('Finished running DAN')


    # for i in range(10):
    #     #     c = all_choices[-i]
    #     #
    #     #     choice_str = TrackerConfig.get_configure_str(c)
    #     #     TrackerConfig.set_configure(c)
    #     #     print('=============================={}.{}=============================='.format(i, choice_str))
    #     #     test(c)
