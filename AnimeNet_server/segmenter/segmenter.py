# -*- coding: utf-8 -*-
import random

import os

#os.environ["CUDA_VISIBLE_DEVICES"]="-1"
import tensorflow as tf
tf.enable_eager_execution()

import cv2 as cv
import sys
import numpy as np

IMG_WIDTH = 64
IMG_HEIGHT = 64

OUT_SIZE = 256

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


def restore_segmenter():
    generator = Generator()
    checkpoint_dir = os.path.join(os.path.dirname(__file__), 'checkpoints')
    checkpoint = tf.train.Checkpoint(generator=generator)
    checkpoint.restore(tf.train.latest_checkpoint(checkpoint_dir))
    return generator

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

def segmentize(generator, photo):
    photo = cv.resize(photo, (IMG_WIDTH, IMG_HEIGHT))
    photo = cv.cvtColor(photo, cv.COLOR_BGRA2BGR)

    photo = np.float32([photo / 127.5 - 1])
    output = generator(photo, training=True)[0]
    output = np.uint8((output + 1) * 127.5)
    output = np.split(output, 4, axis=-1)

    head = cv.resize(output[0], (OUT_SIZE, OUT_SIZE))
    eyes = cv.resize(output[2], (OUT_SIZE, OUT_SIZE))
    hair = cv.resize(output[3], (OUT_SIZE, OUT_SIZE))

    head = equalize_color(head)
    eyes = equalize_color(eyes)
    hair = equalize_color(hair)

    return head, eyes, hair


