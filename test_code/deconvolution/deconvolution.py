import pickle
from time import time
from os.path import dirname, join

import numpy as np
from scipy.misc import toimage

import keras.backend as K
from keras.applications.vgg16 import VGG16
from keras.preprocessing import image

from custom_keras.models import DeconvolutionModel

# VGG16 specific values
MEAN_VALUES = np.array([103.939, 116.779, 123.68])
target_size = (224, 224)

# define output path and make folder
output_path = join(dirname(__file__), 'output')

if K.image_data_format() == 'channels_last':
	ch_dim = 3
else:
	ch_dim = 1


def load_image_from_file(img_name):
	img_path = join(dirname(__file__), 'input', img_name)
	img = image.load_img(img_path)
	img = image.img_to_array(img)

	return img


def deconv_example():
	img_name = 'cat.jpg'
	img = load_image_from_file(img_name)
	
	if K.image_data_format() == 'channels_last':
		input_shape = target_size + (3,)
	else:
		input_shape = (3,) + target_size
	
	conv_model = VGG16(include_top=False, weights='imagenet', input_shape=input_shape)
	
	# print conv info
	# print('\n***CONVOLUTIONAL MODEL INFO***')
	# print('Conv. input shape:', conv_model.input_shape)
	# print('Conv. output shape:', conv_model.output_shape)
	# print('\nLayers in conv. model:')
	# for layer in conv_model.layers:
	# 	print(layer.name)
	
	print('\nCreating deconvolution model')
	start_time = time()
	deconv_model = DeconvolutionModel(conv_model, img, custom_preprocess, custom_postprocess)
	print('\nTime to create was {:.4f} seconds'.format(time() - start_time))
	
	# note that layers are zero indexed
	feat_map_layer_no = 18
	
	choose_max_images = False
	
	print('\nReady for deconv. pred.')
	start_time = time()
	
	if choose_max_images:
		reconstructions_by_feat_map_no, max_imgs_info_by_feat_map_no = deconv_model.produce_reconstructions_from_top_images(feat_map_layer_no, 100, 5, 3)
		# reconstructions_by_feat_map_no, max_imgs_info_by_feat_map_no = deconv_model.produce_reconstruction_from_top_images(feat_map_layer_no, 100, 5, feat_map_nos=[88, 351, 178])
		
		# save reconstructions as images
		for feat_map_no in reconstructions_by_feat_map_no.keys():
			counter = 0
			for rec_array, layer_name, max_img_no in reconstructions_by_feat_map_no[feat_map_no]:
			
				img_to_save = to_savable_image(rec_array)
				
				# save the resulting image to disk
				# avoid scipy.misc.imsave because it will normalize the image pixel value between 0 and 255
				toimage(img_to_save).save(join(dirname(__file__), 'output', 'rec_{}_feat_map_{}_max_{}.png'.format(layer_name, feat_map_no, max_img_no)))
				
				counter += 1
			
		# save max images
		for feat_map_no in max_imgs_info_by_feat_map_no.keys():
			counter = 0
			for rec_array, url in reconstructions_by_feat_map_no[feat_map_no]:
			
				img_to_save = to_savable_image(rec_array)
				
				# save the resulting image to disk
				# avoid scipy.misc.imsave because it will normalize the image pixel value between 0 and 255
				toimage(img_to_save).save(
					join(dirname(__file__), 'max_images', 'feat_map_{}_max_{}.png'.format(feat_map_no, counter)))
				
				counter += 1

		# save reconstructions as pickle
		with open(join(dirname(__file__), 'output', 'deconvolutional_network.pickle'), 'wb') as f:
			pickle.dump(reconstructions_by_feat_map_no, f)
			
		# save max images as pickle
		with open(join(dirname(__file__), 'output', 'max_images.pickle'), 'wb') as f:
			pickle.dump(max_imgs_info_by_feat_map_no, f)
	
	else:
		reconstructions = deconv_model.produce_reconstructions_with_fixed_image(feat_map_layer_no, 10)
		# reconstructions = deconv_model.produce_reconstruction_with_fixed_image(feat_map_layer_no, feat_map_nos=[88, 351, 178, 0, 5])
		
		# save reconstructions as images
		for rec_array, layer_name, feat_map_no in reconstructions:
		
			img_to_save = to_savable_image(rec_array)

			# save the resulting image to disk
			# avoid scipy.misc.imsave because it will normalize the image pixel value between 0 and 255
			toimage(img_to_save).save(join(dirname(__file__), 'output',  'rec_{}_{}.png'.format(layer_name, feat_map_no)))
		
		# save as pickle
		with open(join(dirname(__file__), 'output', 'deconvolutional_network.pickle'), 'wb') as f:
			pickle.dump(reconstructions, f)
	
	print('\nTime to perform reconstructions for feat maps was {:.4f} seconds'.format(time() - start_time))


def custom_preprocess(img_array):
	
	# change size of image
	img = image.array_to_img(img_array)
	height_weight_tuple = (target_size[1], target_size[0])
	if img.size != height_weight_tuple:
		img = img.resize(height_weight_tuple)
		img_array = image.img_to_array(img)

	# change to BGR and subtract mean values
	if K.image_data_format() == 'channels_last':
		img_array = img_array[:, :, ::-1]
		img_array -= MEAN_VALUES.reshape((1, 1, 3))
	else:
		img_array = img_array[::-1, :, :]
		img_array -= MEAN_VALUES.reshape((3, 1, 1))
		
	return img_array


def custom_postprocess(img_array):
	# add mean values
	img_array += MEAN_VALUES.reshape((1, 1, 3))
	
	# change back to RGB
	img_array = img_array[:, :, ::-1]

	return img_array
	
	
# process image to be saved
def to_savable_image(rec_array):
	# use ch_dim - 1 as we have removed batch dimension
	if rec_array.shape[ch_dim - 1] == 1:
		# if greyscale image, remove inner dimension before save
		if K.image_data_format() == 'channels_last':
			rec_array = rec_array.reshape(rec_array.shape[:2])
		else:
			rec_array = rec_array.reshape(rec_array.shape[1:])
	
	return rec_array


deconv_example()
