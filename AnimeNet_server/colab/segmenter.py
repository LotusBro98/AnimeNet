# -*- coding: utf-8 -*-
"""Segmenter.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1st10k_GA4xg1DIvFrqkgZ_AnTzzzE2f8
"""

!pip install pypdn

#!/usr/bin/python3
# Import TensorFlow >= 1.10 and enable eager execution
import random
 
import tensorflow as tf
tf.enable_eager_execution()
 
import os
import time
import numpy as np
import matplotlib.pyplot as plt
import PIL
import sys
import cv2 as cv
import pypdn

from IPython.display import clear_output

from google.colab import drive

mount_folder = '/content/gdrive'
drive.mount(mount_folder, True)

app_folder = mount_folder + "/My Drive/AnimeNet/"

os.chdir(app_folder)

TRAIN_PATH = os.path.join(app_folder, 'face_segmented/')
TEST_PATH = os.path.join(app_folder, 'face_2/')
SAMPLE_DIR = os.path.join(app_folder, 'face_segmented_gen_human')
 
TEST_SIZE = 100
FULL_SIZE = 2000
 
 
LAMBDA = 100
 
EPOCHS = 20
 
BUFFER_SIZE = 400
BATCH_SIZE = 100
IMG_WIDTH = 64
IMG_HEIGHT = 64

!mkdir -p "{SAMPLE_DIR}"

def load_image(image_file, is_train):
    if is_train:
        image = pypdn.read(image_file)
 
        input_image = image.layers[0].image[:,:,:3]
        input_image = cv.cvtColor(input_image, cv.COLOR_RGB2BGR)
        input_image = (input_image / 127.5) - 1
        input_image = np.asarray([input_image], dtype=np.float32)
 
        target_images = []
        for layer in image.layers[1:]:
            layer_image = cv.cvtColor(layer.image, cv.COLOR_RGBA2BGRA)
            target_images.append(np.asarray([layer_image]))
        target_image = np.concatenate(target_images, axis=-1)
        target_image = (target_image / 127.5) - 1
 
        return input_image, target_image
    else:
        input_image = cv.imread(image_file)
        input_image = (input_image / 127.5) - 1
        input_image = np.asarray([input_image], dtype=np.float32)
        return input_image

def save_sample(input, output, filename):
    n_layers = output.shape[3] // 4
    input = cv.cvtColor(input[0], cv.COLOR_BGR2BGRA)
    layers = [input]
    for i in range(n_layers):
        layer = output[0,:,:,i*4:(i+1)*4].numpy()
        layers.append(layer)
    sample = np.hstack(layers)
    sample = (sample + 1) * 127.5
    cv.imwrite(filename, sample)

def process_and_save(dataset, dir):
    cnt = 0
    len_all = len(dataset)
    for input in dataset:
        output = generator(input, training=True)
        filename = os.path.join(dir, "{}.png".format(cnt))
        sys.stdout.write("\r{} / {}".format(cnt, len_all))
        sys.stdout.flush()
        cnt += 1
        save_sample(input, output, filename)
    print()

train_dataset = []
for file in os.listdir(TRAIN_PATH):
    train_dataset.append(load_image(os.path.join(TRAIN_PATH, file), is_train=True))
 
test_dataset = []
test_files = os.listdir(TEST_PATH)[:100]
random.shuffle(test_files)
test_files = test_files[:TEST_SIZE]
for file in test_files:
    test_dataset.append(load_image(os.path.join(TEST_PATH, file), is_train=False))
 
full_dataset = []
full_files = os.listdir(TEST_PATH)
random.shuffle(full_files)
full_files = full_files[:FULL_SIZE]
for file in full_files:
    full_dataset.append(load_image(os.path.join(TEST_PATH, file), is_train=False))

OUTPUT_CHANNELS = 4
OUTPUT_LAYERS = 4

class Downsample(tf.keras.Model):
     
  def __init__(self, filters, size, apply_batchnorm=True):
    super(Downsample, self).__init__()
    self.apply_batchnorm = apply_batchnorm
    initializer = tf.random_normal_initializer(0., 0.02)
 
    self.conv1 = tf.keras.layers.Conv2D(filters, 
                                        (size, size), 
                                        strides=2, 
                                        padding='same',
                                        kernel_initializer=initializer,
                                        use_bias=False)
    if self.apply_batchnorm:
        self.batchnorm = tf.keras.layers.BatchNormalization()
   
  def call(self, x, training):
    x = self.conv1(x)
    if self.apply_batchnorm:
        x = self.batchnorm(x, training=training)
    x = tf.nn.leaky_relu(x)
    return x

class Upsample(tf.keras.Model):
     
  def __init__(self, filters, size, apply_dropout=False):
    super(Upsample, self).__init__()
    self.apply_dropout = apply_dropout
    initializer = tf.random_normal_initializer(0., 0.02)
 
    self.up_conv = tf.keras.layers.Conv2DTranspose(filters, 
                                                   (size, size), 
                                                   strides=2, 
                                                   padding='same',
                                                   kernel_initializer=initializer,
                                                   use_bias=False)
    self.batchnorm = tf.keras.layers.BatchNormalization()
    if self.apply_dropout:
        self.dropout = tf.keras.layers.Dropout(0.5)
 
  def call(self, x12, training):
    x1, x2 = x12
    x = self.up_conv(x1)
    x = self.batchnorm(x, training=training)
    if self.apply_dropout:
        x = self.dropout(x, training=training)
    x = tf.nn.relu(x)
    x = tf.concat([x, x2], axis=-1)
    return x

class Generator(tf.keras.Model):
     
  def __init__(self):
    super(Generator, self).__init__()
    initializer = tf.random_normal_initializer(0., 0.02)
     
    self.down1 = Downsample(64, 4, apply_batchnorm=False)
    self.down2 = Downsample(128, 4)
    self.down3 = Downsample(256, 4)
    self.down4 = Downsample(512, 4)
    self.down5 = Downsample(512, 4)
    self.down6 = Downsample(512, 4)
    self.down7 = Downsample(512, 4)
    self.down8 = Downsample(512, 4)
 
    #self.up1 = Upsample(512, 4, apply_dropout=True)
    self.up2 = Upsample(512, 4, apply_dropout=True)
    self.up3 = Upsample(512, 4, apply_dropout=True)
    self.up4 = Upsample(512, 4)
    self.up5 = Upsample(256, 4)
    self.up6 = Upsample(128, 4)
    self.up7 = Upsample(64, 4)
 
    self.last = tf.keras.layers.Conv2DTranspose(OUTPUT_CHANNELS * OUTPUT_LAYERS,
                                                (4, 4), 
                                                strides=2, 
                                                padding='same',
                                                kernel_initializer=initializer)
  @tf.contrib.eager.defun
  def call(self, x, training):
    # x shape == (bs, 256, 256, 3)    
    x1 = self.down1(x, training=training) # (bs, 128, 128, 64)
    x2 = self.down2(x1, training=training) # (bs, 64, 64, 128)
    x3 = self.down3(x2, training=training) # (bs, 32, 32, 256)
    x4 = self.down4(x3, training=training) # (bs, 16, 16, 512)
    x5 = self.down5(x4, training=training) # (bs, 8, 8, 512)
    x6 = self.down6(x5, training=training) # (bs, 4, 4, 512)
    x7 = self.down7(x6, training=training) # (bs, 2, 2, 512)
    x8 = self.down8(x7, training=training) # (bs, 1, 1, 512)
 
    #x9 = self.up1((x8, x7), training=training) # (bs, 2, 2, 1024)
    #x10 = self.up2((x8, x6), training=training) # (bs, 4, 4, 1024)
    x11 = self.up3((x8, x5), training=training) # (bs, 8, 8, 1024)
    x12 = self.up4((x11, x4), training=training) # (bs, 16, 16, 1024)
    x13 = self.up5((x12, x3), training=training) # (bs, 32, 32, 512)
    x14 = self.up6((x13, x2), training=training) # (bs, 64, 64, 256)
    x15 = self.up7((x14, x1), training=training) # (bs, 128, 128, 128)
 
    x16 = self.last(x15) # (bs, 256, 256, 3)
    x16 = tf.nn.tanh(x16)
 
    return x16

def generator_loss(gen_output, target):
  l1_loss = tf.reduce_mean(tf.abs(target - gen_output))
 
  total_gen_loss = LAMBDA * l1_loss
 
  return total_gen_loss

generator_optimizer = tf.train.AdamOptimizer(2e-4, beta1=0.5)

def generate_images(model, test_input, tar):
  prediction = model(test_input, training=True)
  prediction0 = np.uint8((prediction + 1) * 127.5)[0]
 
  test_input = np.uint8((test_input + 1) * 127.5)[0]
 
  head_layer = prediction0[:,:,0:4]
  mouth_layer = prediction0[:,:,4:8]
  eyes_layer = prediction0[:, :, 8:12]
  hair_layer = prediction0[:, :, 12:16]
 
  #segments = eyes_layer + hair_layer
 
  clear_output(wait=True)
  
  plt.subplot(1, 5, 1)
  plt.imshow(cv.cvtColor(test_input, cv.COLOR_BGR2RGB))
  plt.subplot(1, 5, 2)
  plt.imshow(cv.cvtColor(head_layer, cv.COLOR_BGR2RGB))
  plt.subplot(1, 5, 3)
  plt.imshow(cv.cvtColor(mouth_layer, cv.COLOR_BGR2RGB))
  plt.subplot(1, 5, 4)
  plt.imshow(cv.cvtColor(eyes_layer, cv.COLOR_BGR2RGB))
  plt.subplot(1, 5, 5)
  plt.imshow(cv.cvtColor(hair_layer, cv.COLOR_BGR2RGB))
  plt.show()
#   cv.imshow("Head", head_layer)
#   cv.imshow("Mouth", mouth_layer)
#   cv.imshow("Eyes", eyes_layer)
#   cv.imshow("Hair", hair_layer)
  #cv.imshow("Segments", segments)
  #cv.waitKey(10)

def train(model, dataset, epochs):
  for epoch in range(epochs):
    start = time.time()
 
    cnt = 0
    for input, target in dataset:
 
      with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        gen_output = model(input, training=True)
 
        gen_loss = generator_loss(gen_output, target)
 
      generator_gradients = gen_tape.gradient(gen_loss, 
                                              generator.variables)
 
      generator_optimizer.apply_gradients(zip(generator_gradients, 
                                              generator.variables))
       
      sys.stdout.write(str(cnt) + " ")
      sys.stdout.flush()
 
      #if cnt % 10 == 4:
      cnt += 1
    index = np.random.randint(0, len(test_dataset) - 1)
    generate_images(model, test_dataset[index], None)
 
      
           
    print()
 
    print ('Time taken for epoch {} is {} sec\n'.format(epoch + 1,
                                                        time.time()-start))
 
  checkpoint.save(file_prefix=checkpoint_prefix)

generator = Generator()

checkpoint_dir = os.path.join(app_folder, 'segmenter_checkpoints')
checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
checkpoint = tf.train.Checkpoint(generator=generator)

checkpoint.restore(tf.train.latest_checkpoint(checkpoint_dir))

!rm -rf "{SAMPLE_DIR}"/*
process_and_save(full_dataset, SAMPLE_DIR)

train(generator, train_dataset, 100)

import cv2 as cv
import os
import sys
from google.colab.patches import cv2_imshow
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline

def equalize_color(label):
  mask = label[:,:,3] // 128
  label = np.transpose(label, (2, 0, 1))
  label *= mask
  color = np.sum(label, axis=(1, 2)) / np.sum(mask)
  color[3] = 255
  label = color * np.transpose(np.repeat([mask], 4, axis = 0), (1, 2, 0))
  label = np.transpose(label, (2, 0, 1))
  label[:3] += 255*(1-mask)
  label = np.transpose(label, (1, 2, 0))
  label = np.uint8(label)
  return label

def blend(label1, label2):
  mask1 = label1[:,:,3] // 128
  mask2 = label2[:,:,3] // 128
  label1 = np.transpose(label1, (2, 0, 1))
  label2 = np.transpose(label2, (2, 0, 1))
  label = label1 * (1 - mask2) + label2 * (mask2)
  label = np.transpose(label, (1, 2, 0))
  return label
  
os.chdir(app_folder)

INPUT_PATH = "face_segmented_gen_human/"
OUTPUT_PAIRS_TEST = "anime_dataset_7/test_pair_human/{}.png"

!mkdir -p "anime_dataset_7/test_pair_human"
!rm -rf "anime_dataset_7/test_pair_human/*"

cnt = 0
all_len = len(os.listdir(INPUT_PATH))
for filename in os.listdir(INPUT_PATH):
  img = cv.imread(INPUT_PATH + filename, cv.IMREAD_UNCHANGED)
  
  w = img.shape[1] // 5
  
  out_image = img[:,:w]
  label_head = img[:, w:2*w]
  label_mouth = img[:, 2*w:3*w]
  label_eyes = img[:, 3*w:4*w]
  label_hair = img[:, 4*w:5*w]
  
  label_head = equalize_color(label_head)
  label_mouth = equalize_color(label_mouth)
  label_eyes = equalize_color(label_eyes)
  label_hair = equalize_color(label_hair)
  
  out_label = blend(label_head, label_mouth)
  out_label = blend(out_label, label_eyes)
  out_label = blend(out_label, label_hair)
  
  #plt.imshow(cv.cvtColor(out_label, cv.COLOR_BGR2RGB))
  #break 
  
  out_label = np.hstack([label_head, label_eyes, label_hair])

  out_image = cv.resize(out_image, (64, 64))
  out_label = cv.resize(out_label, (192, 64))

  out_pair = np.hstack([out_image , out_label])
  
  cv.imwrite(OUTPUT_PAIRS_TEST.format(cnt), out_pair)
  sys.stdout.write("\rTEST: {} / {}".format(cnt, all_len))
  sys.stdout.flush()
  cnt += 1
print()

!wget https://www.crcv.ucf.edu/data/Selfie/Selfie-dataset.tar.gz

!cd selfies && tar -xf Selfie*

#!mkdir -p face_2
!rm -rf anime_dataset_7/test_pair_human/*
!ls anime_dataset_7/test_pair_human/

SELFIES_PATH = "selfies/Selfie-dataset/images"
OUTPUT_PATH = "face_2"


files = os.listdir(SELFIES_PATH)
random.shuffle(files)
files = files[:500]

SCALE = 1.3

cnt = 0
for file in files:
  path = os.path.join(SELFIES_PATH, file)
  img = cv.imread(path)
  
  H, W = img.shape[0:2]
  
  cascade = cv.CascadeClassifier("haarcascade_frontalface_default.xml")
  faces = cascade.detectMultiScale(img)
  if (len(faces) == 0):
    continue
  x, y, w, h = faces[0]
  
  x -= w * (SCALE - 1) / 2
  y -= h * (SCALE - 1) / 2
  y += h * 0.1
  
  w *= SCALE
  h *= SCALE
  
  x = int(x)
  y = int(y)
  w = int(w)
  h = int(h)
  
  if x < 0 or y < 0 or x + w >= W or y + h >= H:
    continue
  
  face = img[y:y+h, x:x+w]
  face = cv.resize(face, (64, 64))
  
  #plt.imshow(cv.cvtColor(face, cv.COLOR_BGR2RGB))
  #plt.show()
  #plt.pause(0.001)
  
  cv.imwrite(os.path.join(OUTPUT_PATH, "{}.png".format(cnt)), face)
  cnt += 1
  sys.stdout.write("\r"+str(cnt))

