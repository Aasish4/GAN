# -*- coding: utf-8 -*-
"""GAN.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10OvAZCaiB2kYQzXvRFLTQbCxf-KKVgYE
"""

!ln -s '/content/drive/MyDrive/My project' '/content/proj'

# Commented out IPython magic to ensure Python compatibility.
# %cd /content/proj

import cv2
import numpy as np
import matplotlib.pyplot as plt
from os import listdir
from keras.models import Sequential
from keras.optimizers import Adam
from keras.layers import Dense, Conv2D, Flatten, Reshape, Conv2DTranspose
from keras.layers import LeakyReLU, Dropout
from keras.utils import plot_model
from keras.preprocessing.image import ImageDataGenerator
from keras.models import load_model
from tqdm import tqdm

def load_images(directory, n):
  images = []
  i=0
  for file in tqdm(sorted(listdir(directory)), total=n-1):
    filename = directory + file
    image = cv2.imread(filename)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = np.asarray(image)
    images.append(image)
    i += 1
    if i >= n:
      break
  return np.asarray(images)

images = load_images('/content/proj/cropped/', 25)

for i in range(25):
  plt.subplot(5,5,i+1)
  plt.axis('off')
  plt.imshow(images[i])
plt.show()

def discriminator(in_shape=(128,128,3)):
  model = Sequential()
  model.add(Conv2D(64, (3,3), padding='same', input_shape=in_shape))
  model.add(LeakyReLU(alpha=0.2))
  model.add(Conv2D(64, (3,3), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))
  model.add(Conv2D(64, (3,3), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))
  model.add(Conv2D(64, (3,3), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))
  model.add(Conv2D(64, (3,3), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))

  model.add(Flatten())
  model.add(Dropout(0.4))
  model.add(Dense(1, activation='sigmoid'))
  opt = Adam(learning_rate=0.0002, beta_1=0.5)
  model.compile(loss='binary_crossentropy', optimizer=opt, metrics=['accuracy'])

  return model

model_D = discriminator()

model_D.summary()

def generator(latent_dim):
  model = Sequential()
  # for an 8 * 8 image
  n_nodes = 256*8*8
  model.add(Dense(n_nodes, input_dim=latent_dim))
  model.add(LeakyReLU(alpha=0.2))
  model.add(Reshape((8,8,256)))

  # upsample to 16*16
  model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))

  # upsample to 32x32
  model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))

  # upsample to 64x64
  model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))

  # upsample to 128x128
  model.add(Conv2DTranspose(128, (4,4), strides=(2,2), padding='same'))
  model.add(LeakyReLU(alpha=0.2))

  model.add(Conv2D(3, (7,7), activation='tanh', padding='same'))

  return model

model_G = generator(100)
model_G.summary()

def GAN(model_G, model_D):
  model_D.trainable=False
  model = Sequential()
  model.add(model_G)
  model.add(model_D)
  opt = Adam(learning_rate=0.0002, beta_1=0.5)
  model.compile(loss='binary_crossentropy', optimizer=opt)
  return model

model_gan = GAN(model_G, model_D)
model_gan.summary()

def load_real_images():
  datagen = ImageDataGenerator(rescale=1./255)
  X = datagen.flow_from_directory('/content/proj/test',
                                  target_size= (128,128),
                                  batch_size= 1200,
                                  class_mode='binary')
  data_list = []
  batch_index = 0
  while batch_index <= X.batch_size:
    data = X.next()
    data_list.append(data[0])
    batch_index += 1
  img_array = np.asarray(data_list)
  return img_array

def generate_real_img(dataset, n_samples):
  i = np.random.randint(0, dataset.shape[0], n_samples)
  X = dataset[i]
  y = np.ones((n_samples, 1))
  return X, y

def generate_latent_points(latent_dim, n_samples):
  X = np.random.randn(latent_dim * n_samples)
  X = X.reshape(n_samples, latent_dim)
  return X

def generate_fake_images(model_G, latent_dim, n_samples):
  X_input = generate_latent_points(latent_dim, n_samples)
  X = model_G.predict(X_input)
  y = np.zeros((n_samples, 1))
  return X, y

def summarize(epoch, model_G, model_D, dataset, latent_dim, n_samples=100):
  model_G.save('./model/' +str(epoch)+ '.h5')
  x_real, y_real = generate_real_img(dataset, n_samples)
  _, acc_real = model_D.evaluate(x_real, y_real, verbose=0)

  x_fake, y_fake = generate_fake_images(model_G, latent_dim, n_samples)
  _, acc_fake = model_D.evaluate(x_fake, y_fake, verbose=0)

  print('Accuracy real: %.0f%%, fake: %.0f%%' % (acc_real*100, acc_fake*100))

def train_GAN(model_G, model_D, model_GAN, dataset, latent_dim, n_epochs=500, n_batch=128 ):
  bat_per_epo = int(dataset.shape[0]/ n_batch)

  for i in range(n_epochs):
    for j in range(bat_per_epo):
      x_real, y_real = generate_real_img(dataset, n_batch)
      x_fake, y_fake = generate_fake_images(model_G, latent_dim, n_batch)

      x, y = np.vstack((x_real, x_fake)), np.vstack((y_real, y_fake))

      d_loss, _ = model_D.train_on_batch(x, y)
      x_gan = generate_latent_points(latent_dim, n_batch)
      y_gan = np.ones((n_batch, 1))

      g_loss = model_GAN.train_on_batch(x_gan, y_gan)

      print('epoch: %d, batch:%d/%d, d_loss=%.3f, g_loss=%.3f' %(i+1, j+1, bat_per_epo, d_loss, g_loss))
    if (i+1) % 10 == 0:
      summarize(i, model_G, model_D, dataset, latent_dim)

latent_dim = 10
model_D = discriminator()
model_G = generator(latent_dim)
model_GAN = GAN(model_G, model_D)

dataset = load_real_images()

train_GAN(model_G, model_D, model_GAN, dataset[0], latent_dim)

def plot_images(images, n):
  images = (images-images.min())/(images.max() - images.min())
  for i in range(n):
    plt.subplot(1,n,1+i)
    plt.axis('off')
    plt.imshow(images[i, :, :])
  plt.show()

pts = generate_latent_points(10,50)
X = model_G.predict(pts)
plot_images(X, 9)

