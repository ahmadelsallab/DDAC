import numpy as np
import math
from keras.initializations import normal, identity
from keras.models import model_from_json
from keras.models import Sequential, Model
from keras.engine.training import collect_trainable_weights
from keras.layers import Dense, Flatten, Input, merge, Lambda
from keras.optimizers import Adam
import tensorflow as tf
import keras.backend as K

HIDDEN1_UNITS = 300
HIDDEN2_UNITS = 600

class ActorNetwork(object):
    def __init__(self, sess, state_size, action_size, BATCH_SIZE, TAU, LEARNING_RATE):
        self.sess = sess
        self.BATCH_SIZE = BATCH_SIZE
        self.TAU = TAU
        self.LEARNING_RATE = LEARNING_RATE

        K.set_session(sess)

        #Now create the model
        self.model , self.weights, self.state = self.create_actor_network(state_size, action_size)   
        self.target_model, self.target_weights, self.target_state = self.create_actor_network(state_size, action_size) 
        self.action_gradient = tf.placeholder(tf.float32,[None, action_size])
        self.params_grad = tf.gradients(self.model.output, self.weights, -self.action_gradient)
        grads = zip(self.params_grad, self.weights)
        #self.optimize = tf.train.AdamOptimizer(LEARNING_RATE).apply_gradients(grads*(self.prev_action - self.model.output)) # Favor the previous actions, discourage actions change
		self.optimize = tf.train.AdamOptimizer(LEARNING_RATE).apply_gradients(grads) # Favor the previous actions, discourage actions change
        self.sess.run(tf.initialize_all_variables())

    def train(self, states, action_grads):
        self.sess.run(self.optimize, feed_dict={
            self.state: states,
			self.action_gradient: action_grads
            #self.action_gradient: action_grads, state: self.prev_actions # Keep prev_actions as state variables
        })

    def target_train(self):
        actor_weights = self.model.get_weights()
        actor_target_weights = self.target_model.get_weights()
        for i in xrange(len(actor_weights)):
            actor_target_weights[i] = self.TAU * actor_weights[i] + (1 - self.TAU)* actor_target_weights[i]
        self.target_model.set_weights(actor_target_weights)

    def create_actor_network(self, state_size,action_dim):
        print("Now we build the model")
        S = Input(shape=[state_size])   
        h0 = Dense(HIDDEN1_UNITS, activation='relu')(S)
        h1 = Dense(HIDDEN2_UNITS, activation='relu')(h0)
        Steering = Dense(1,activation='tanh',init=lambda shape, name: normal(shape, scale=1e-4, name=name))(h1)  
        Acceleration = Dense(1,activation='sigmoid',init=lambda shape, name: normal(shape, scale=1e-4, name=name))(h1)   
        Brake = Dense(1,activation='sigmoid',init=lambda shape, name: normal(shape, scale=1e-4, name=name))(h1) 
        V = merge([Steering,Acceleration,Brake],mode='concat')          
        model = Model(input=S,output=V)
		
		model = Sequential()

		# CNN
		# number of convolutional filters to use
		nb_filters = 32
		# size of pooling area for max pooling
		pool_size = (2, 2)
		# convolution kernel size
		kernel_size = (3, 3)
		
		nb_epoch = 100
		batch_size = 100
		
		model.add(Convolution2D(nb_filters, kernel_size[0], kernel_size[1],
								border_mode='valid',
								input_shape=[state_size]))
		model.add(Activation('relu'))
		model.add(Convolution2D(nb_filters, kernel_size[0], kernel_size[1]))
		model.add(Activation('relu'))
		model.add(MaxPooling2D(pool_size=pool_size))
		model.add(Dropout(0.25))

		model.add(Flatten())
		model.add(Dense(HIDDEN1_UNITS))
		model.add(Activation('relu'))
		model.add(Dropout(0.5))
		#model.add(Dense(nb_classes))
		#model.add(Activation('softmax'))
		
		'''
		model.compile(loss='categorical_crossentropy',
              optimizer='adadelta',
              metrics=['accuracy'])
		
		model.fit(S, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          verbose=1)
        '''
		return model, model.trainable_weights, S

