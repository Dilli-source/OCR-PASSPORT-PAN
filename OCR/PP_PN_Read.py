
import json
import ftfy
import io
from passporteye import read_mrz
import re
import cv2
import pytesseract
import numpy as np
from PIL import Image as im
from PIL import Image, ImageEnhance, ImageGrab
import os
import datetime                                       # Imported package for date and time process
from datetime import datetime
import threading                                      # Imported package for Threading Functionality
from concurrent.futures import ThreadPoolExecutor     # Imported package for pooling the thread
import time
import boto3
from pdf2image import convert_from_path

def pdf_to_jpg(input_file):
    try:
        images = convert_from_path(input_file,first_page=1, last_page=1)
        count=0
        for i, image in enumerate(images):
            image.save(f'{input_file}_page_{i+1}.jpg', 'JPEG')
        return True
    except Exception as e:
        print("Error during PDF Conversion")
        print(e)

def image_extractor_function(file_to_process):
    print("Entered Image Extraction")
    pytesseract.pytesseract.tesseract_cmd='tesseract'
    StrText = []
    time.sleep(3)
    actual_filename=file_to_process.split('/')[-1]
    received_filename=actual_filename.split('.')[0]
    filename=(file_to_process)
    def convert_image_hd(img_convert):
        # Convert the image to RGB mode if it is not already in that mode
        new_size = (3840, 2160)
        # Resize the image to the new size using Lanczos resampling
        im_resized = img_convert.resize(new_size, resample=Image.LANCZOS)
        return im_resized
    pdf_flag=0
    if os.path.splitext(filename)[1].lower() == '.png':
        print("PNG Image Received")
        # Open the PNG file
        with Image.open(filename) as image_convert:
            if image_convert.mode != 'RGB':
                converted_im = image_convert.convert('RGB')
                im_resized=convert_image_hd(converted_im)
                file_to_save=str(os.getcwd())+"/Passport_images/Processed/"+str(filename)[1].lower()+'_stage1.jpg'
                # Save the resized image as a JPG file with quality set to 95
                im_resized.save(file_to_save, quality=98)
                im1 = Image.open(file_to_save)
    elif os.path.splitext(filename)[1].lower() == '.jpg':
        print("jpg Image Received")
        im1 = Image.open(filename)
    elif os.path.splitext(filename)[1].lower() == '.pdf':
        print("It is a PDF Document")
        flag=pdf_to_jpg(filename)
        pdf_flag=1
        if flag==True:
            im1 = Image.open(f'{filename}_page_1.jpg')
      #function to remove file from path
    def remove_file(image_remove_file):
        if os.path.exists(image_remove_file):
            os.remove(image_remove_file)
        return True
    # Function for creating thread process
    def fn_start_thread_processing_org(remove_path_file) :
        try:
            assign_thread = threading.Thread(target=remove_file,args=(remove_path_file,))
            assign_thread.setDaemon( True )
            assign_thread.start()
            time.sleep(10)
            assign_thread.join()
        except Exception as e:
            print("Error in Thread Creation function",e)
            exit()
    # Main Function to create Thread Pool Executor
    def code_runner(remove_path_file):
        try:
            # Function to Create to Thread Pool Executor to create threads
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.submit(fn_start_thread_processing_org,remove_path_file)
        except Exception as e:
            print("Error in Multithreading function",e)
            exit()
    IdleImg1 = np.asarray(im1)
    r, g, b = cv2.split (IdleImg1)
    g1=cv2.merge([b, g, r])
    img = cv2.cvtColor (g1, cv2.COLOR_BGR2GRAY)
    img = cv2.medianBlur(img, 3)
    # Apply Gaussian blur to the image to remove noise
    img = cv2.GaussianBlur(img, (5, 5), 0)
    # Apply histogram equalization to enhance the contrast
    #equ_img = cv2.equalizeHist(img)
    data = im.fromarray(img)
    # Create an enhancer object for brightness
    brightness = ImageEnhance.Brightness(data)
    # Increase the brightness by a factor of 0.5
    img_with_brightness = brightness.enhance(0.5)
    # Create an enhancer object for sharpness
    sharpness = ImageEnhance.Sharpness(img_with_brightness)
    # Increase the sharpness by a factor of 5
    img_with_sharpness = sharpness.enhance(10)
    contrast = ImageEnhance.Contrast(img_with_sharpness)
    # Increase the contrast by a factor of 4
    img_with_contrast = contrast.enhance(2)
    # Save the modified image
    print("processed stage 1")
    img_with_contrast.save(str(os.getcwd())+"/Passport_images/Processed/"+str(received_filename)+'_stage2.jpg')
    path_to_remove_file=str(os.getcwd())+"/Passport_images/"+str(actual_filename)
    code_runner(path_to_remove_file)
    if pdf_flag==1:
        code_runner(f'{filename}_page_1.jpg')
    print("removed stage 1 image")
    def is_date(string, format="%d-%m-%Y"):
        try:
            datetime.strptime(string, format)
            return True
        except ValueError:
            return False
    def preprocess_dict_fn(received_dict):
        for each_element in received_dict:
            if each_element=="names":
                #print(received_dict[each_element])
                k_filtered_name=re.sub(r"K{2,}", "", received_dict[each_element])
                filtered_name=re.sub(r"<", "", k_filtered_name)
                #received_dict[each_element]=filtered_name
                g_filtered_name = re.sub(r"G{2,}", "", filtered_name)
                double_k_filtered_name=re.sub(r'\s+K\s+K', '', g_filtered_name)
                spaces_k_filtered_name=re.sub(r' {3,}K', '', double_k_filtered_name)
                spaces_special_filtered_name = re.sub(r'[^\w\s]', '', spaces_k_filtered_name)
                spaces_E_filtered_name = re.sub(r'[^\w\s]|(?<=\s)\s{3,}', '', spaces_special_filtered_name)
                spaces_A_filtered_name = re.sub(r' {3,}A', '', spaces_E_filtered_name)
                spaces_E_filtered_name = re.sub(r' {3,}E', '', spaces_A_filtered_name)
                received_dict[each_element] = spaces_E_filtered_name
            if each_element=="number":
                #print(received_dict[each_element])
                k_filtered_number = re.sub(r"K{2,}", "", received_dict[each_element])
                filtered_number = re.sub(r"<", "", k_filtered_number)
                received_dict[each_element] = filtered_number
            if each_element=="date_of_birth":
                #print(received_dict[each_element])
                try:
                    if received_dict[each_element].isdigit():
                        date = datetime.strptime(received_dict[each_element], "%y%m%d")

                        formatted_date_dob=date.strftime("%d-%m-%Y")

                        if is_date(formatted_date_dob):
                            received_dict[each_element] = formatted_date_dob
                        else:
                            received_dict[each_element] = ""
                    else:
                        received_dict[each_element] = ""
                except Exception as e:
                    print(e)
            if each_element=="expiration_date":
                #print(received_dict[each_element])
                try:
                    if received_dict[each_element].isdigit():
                        date = datetime.strptime(received_dict[each_element], "%y%m%d")

                        formatted_date_expiry=date.strftime("%d-%m-%Y")
                        if is_date(formatted_date_expiry):
                             received_dict[each_element] = formatted_date_expiry
                        else:
                            received_dict[each_element] = ""
                    else:
                        received_dict[each_element] = ""
                except Exception as e:
                    print(e)
            if each_element=="surname":
                #print(received_dict[each_element])
                k_filtered_surname = re.sub(r"K{2,}", "", received_dict[each_element])
                filtered_surname = re.sub(r"<", "", k_filtered_surname)
                received_dict[each_element] = filtered_surname
        return received_dict
    try:
        # Create a defaultdict with a default value of "Not Found"
        default_dict={"response":"Image is not clear"}
        # Process image
        processed_image_path=str(os.getcwd())+"/Passport_images/Processed/"+str(received_filename)+'_stage2.jpg'
        print("reading the mrz data")
        mrz = read_mrz(processed_image_path)
        print("Data Read Successfully")
        # Obtain image
        mrz_data = mrz.to_dict()
        code_runner(processed_image_path)
        print("Deleted the stage 2 image")
        print("preprocessing started")
        processed_dict=preprocess_dict_fn(mrz_data)
        print("preprocessed")
        #print(processed_dict)
        return processed_dict
    except Exception as e:
        print(e)
        return (default_dict)
#function to remove file from path
def fn_remove_file(image_remove_file):
    if os.path.exists(image_remove_file):
        os.remove(image_remove_file)
    return True
# Function for creating thread process
def fn_start_thread_processing_org_pan(remove_path_file) :
    try:
        assign_thread = threading.Thread(target=fn_remove_file,args=(remove_path_file,))
        assign_thread.setDaemon( True )
        assign_thread.start()
        time.sleep(10)
        assign_thread.join()
    except Exception as e:
        print("Error in Thread Creation function",e)
        exit()
# Main Function to create Thread Pool Executor
def code_runner_pan(remove_path_file):
    try:
        # Function to Create to Thread Pool Executor to create threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.submit(fn_start_thread_processing_org_pan,remove_path_file)
    except Exception as e:
        print("Error in Multithreading function",e)
        exit()
def findword(textlist, wordstring):
    lineno = -1
    for wordline in textlist:
        xx = wordline.split( )
        if ([w for w in xx if re.search(wordstring, w)]):
            lineno = textlist.index(wordline)
            textlist = textlist[lineno+1:]
            return textlist
    return textlist
def pan_read_data(text):
    name = None
    fname = None
    dob = None
    pan = None
    nameline = []
    dobline = []
    panline = []
    text0 = []
    text1 = []
    text2 = []
    lines = text.split('\n')
    for lin in lines:
        s = lin.strip()
        s = lin.replace('\n','')
        s = s.rstrip()
        s = s.lstrip()
        text1.append(s)
    text1 = list(filter(None, text1))
    lineno = 0
    for wordline in text1:
            xx = wordline.split('\n')
            if ([w for w in xx if re.search('(INCOMETAXDEPARWENT|INCOME|TAX|GOW|GOVT|GOVERNMENT|OVERNMENT|VERNMENT|DEPARTMENT|EPARTMENT|PARTMENT|ARTMENT|INDIA|NDIA)$', w)]):
                text1 = list(text1)
                lineno = text1.index(wordline)
                break
    text0 = text1[lineno+1:]
    try:
        # Cleaning first names
        name = text0[0]
        #print(name)
        name = name.rstrip()
        name = name.lstrip()
        name = name.replace("8", "B")
        name = name.replace("0", "D")
        name = name.replace("6", "G")
        name = name.replace("1", "I")
        name = re.sub('[^a-zA-Z] +', ' ', name)
        # Cleaning Father's name
        fname = text0[1]
        fname = fname.rstrip()
        fname = fname.lstrip()
        fname = fname.replace("8", "S")
        fname = fname.replace("0", "O")
        fname = fname.replace("6", "G")
        fname = fname.replace("1", "I")
        fname = fname.replace("\"", "A")
        fname = re.sub('[^a-zA-Z] +', ' ', fname)
        # Cleaning DOB
        dob = text0[2][:10]
        dob = dob.rstrip()
        dob = dob.lstrip()
        dob = dob.replace('l', '/')
        dob = dob.replace('L', '/')
        dob = dob.replace('I', '/')
        dob = dob.replace('i', '/')
        dob = dob.replace('|', '/')
        dob = dob.replace('\"', '/1')
        dob = dob.replace(" ", "")
        # Cleaning PAN Card details
        text0 = findword(text1, '(Pormanam|Number|umber|Account|ccount|count|Permanent|ermanent|manent|wumm)$')
        panline = text0[0]
        pan = panline.rstrip()
        pan = pan.lstrip()
        pan = pan.replace(" ", "")
        pan = pan.replace("\"", "")
        pan = pan.replace(";", "")
        pan = pan.replace("%", "L")
        pan=pan.replace("ee","")
        pan=pan.replace("a","")
        pan = re.sub(r'[a-z]', "", pan)
    except:
        pass
    data = {}
    data['Name'] = name
    data['Father Name'] = fname
    data['Date of Birth'] = dob
    data['PAN'] = pan
    data['ID Type'] = "PAN"
    return data
def extraction_pan(trail_id,source_img_path):
    if os.path.splitext(source_img_path)[1].lower() == '.jpg':
        img = cv2.imread(source_img_path)
        img = cv2.resize(img, None, fx=2, fy=2,interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(img, cv2.CV_64F).var()
        if var < 50:
            print("Image is Too Blurry....")
            exit(1)
    elif os.path.splitext(source_img_path)[1].lower() == '.png':
        img = cv2.imread(source_img_path)
        img = cv2.resize(img, None, fx=2, fy=2,interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(img, cv2.CV_64F).var()
        if var < 50:
            print("Image is Too Blurry....")
            exit(1)
    elif os.path.splitext(source_img_path)[1].lower() == '.jpeg':
        img = cv2.imread(source_img_path)
        img = cv2.resize(img, None, fx=2, fy=2,interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        var = cv2.Laplacian(img, cv2.CV_64F).var()
        if var < 50:
            print("Image is Too Blurry....")
            exit(1)
    filename = source_img_path
    pdf_flag=0
    if os.path.splitext(filename)[1].lower() == '.pdf':
        print("It is a PDF Document for PAN")
        flag=pdf_to_jpg(filename)
        pdf_flag=1
        if flag==True:
            im1 = Image.open(f'{filename}_page_1.jpg')
    elif os.path.splitext(filename)[1].lower() == '.jpg':
        im1 = Image.open(filename)
    elif os.path.splitext(filename)[1].lower() == '.png':
        im1 = Image.open(filename)
    elif os.path.splitext(filename)[1].lower() == '.jpeg':
        im1 = Image.open(filename)
    text = pytesseract.image_to_string(im1, lang = 'eng')
    text_output = open(str(trail_id)+'_output.txt', 'w', encoding='utf-8')
    text_output.write(text)
    text_output.close()
    file = open(str(trail_id)+'_output.txt', 'r', encoding='utf-8')
    text = file.read()
    text = ftfy.fix_text(text)
    text = ftfy.fix_encoding(text)
    if pdf_flag==1:
       code_runner_pan(f'{filename}_page_1.jpg')
    data = pan_read_data(text)
    with io.open(str(trail_id)+'_info.json', 'w', encoding='utf-8') as outfile:
        data = json.dumps(data, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
        outfile.write((data))
    with open(str(trail_id)+'_info.json', encoding = 'utf-8') as data:
        data_loaded = json.load(data)
    
    code_runner_pan(str(trail_id)+'_info.json')
    code_runner_pan(str(trail_id)+'_output.txt')
    code_runner_pan(filename)
    return data_loaded
def s3_dowloader_fn(trail_id,Path_to_dowload_file,id_type):
    # Ask the user for an S3 URL to download
    # Split the S3 URL into bucket and key
    ACCESS_KEY = 'AKIA4OK4D4'
    SECRET_KEY = 'XeXkhJnvw+WZR'
    s3 = boto3.client('s3',aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
    parts = Path_to_dowload_file.split('/')
    print(parts)
    bucket = parts[2]
    key = '/'.join(parts[3:])
    print(key)
    if id_type=="PP":
        # Download the file from S3
        passport_result={}
        print("Files are getting downloaded from s3 for Passport")
        try:
            s3.download_file(bucket, key, str(os.getcwd())+"/Passport_images/"+str(key.split('/')[-1]))
            print("file is Downloaded")
            file_to_process=str(os.getcwd())+"/Passport_images/"+str(key.split('/')[-1])
            print("calling the image Extraction function")
            passport_result[trail_id]=image_extractor_function(file_to_process)
            print("Text Extracted")
            return passport_result
        except Exception as e:
            print(f"Error downloading s3 file for Passport: {e}")
    elif id_type=="PN":
        # Download the file from S3
        pan_result={}
        print("Files are getting downloaded from s3 for PAN")
        try:
            s3.download_file(bucket, key, str(os.getcwd())+"/Pan_images/"+str(key.split('/')[-1]))
            print("file is Downloaded")
            pan_file_to_process=str(os.getcwd())+"/Pan_images/"+str(key.split('/')[-1])
            print("calling the image Extraction function")
            pan_result[trail_id]=extraction_pan(trail_id,pan_file_to_process)
            print("Text Extracted")
            return pan_result
        except Exception as e:
            print(f"Error downloading s3 file for pan card: {e}")

