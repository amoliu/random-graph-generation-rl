from layer import *
import tensorflow as tf
import numpy as np
from utils import *
from math import exp

class VAEGCell(object):
    """Variational Auto Encoder cell."""

    def __init__(self, adj, weight, features, z_dim, bin_dim):
        '''
        Args:
        adj : adjacency matrix
	features: feature matrix
	'''
        self.adj = adj
        self.features = features
        self.z_dim = z_dim
        self.weight = weight
        self.name = self.__class__.__name__.lower()
        self.bin_dim = bin_dim
    @property
    def state_size(self):
        return (self.n_h, self.n_h)

    @property
    def output_size(self):
        return self.n_h


    def __call__(self,c_x,n,d,k,eps_passed, sample,scope=None):
        '''
		Args:
			c_x - tensor to be filled up with random walk property
			n - number of nodes 
			d - number of features in the feature matrix
			k - length of random walk
				defaults to be None
    	'''
        with tf.variable_scope(scope or type(self).__name__):
            c_x = input_layer(c_x, self.adj, self.weight, self.features, k, n, d, activation=None, batch_norm=False, istrain=False, scope=None)
            c_x = tf.Print(c_x,[c_x], message="my c_x-values:")
	    
            with tf.variable_scope("Prior"):
                prior_mu = tf.zeros(shape=[n,self.z_dim,1],name="prior_mu") 
                prior_sigma = tf.matrix_diag(tf.ones(shape=[n,self.z_dim]),name="prior_sigma")

	    with tf.variable_scope("Encoder"):
                list_cx = tf.unstack(c_x)
                # output will be of shape n X kd
                enc_hidden = fc_layer(tf.concat(list_cx,1), k*d, activation=tf.nn.relu, scope="hidden")
                #output will be of shape n X 5 (this is a hyper paramater)
		enc_mu = fc_layer(enc_hidden, self.z_dim,activation=tf.nn.softplus, scope='mu')
                enc_mu = tf.reshape(enc_mu, [n,self.z_dim,1])
                enc_mu = tf.Print(enc_mu,[enc_mu], message="my enc_mu-values:")

                # output will be n X 1 then convert that to a diagonal matrix
                debug_sigma = fc_layer(enc_hidden, self.z_dim, activation=tf.nn.softplus, scope='sigma')
	        debug_sigma = tf.Print(debug_sigma,[debug_sigma], message="my debug_sigma-values:")
                enc_sigma = tf.matrix_diag(debug_sigma, name="enc_sigma")
                enc_sigma = tf.Print(enc_sigma,[enc_sigma], message="my enc_sigma-values:")

            # Random sampling ~ N(0, 1)
            eps = eps_passed 
            #eps = tf.random_normal((n, self.z_dim, 1), 0.0, 1.0, dtype=tf.float32)
	    
	    temp_stack = []
	    for i in range(n):
		temp_stack.append(tf.matmul(enc_sigma[i], eps[i]))
	    z = tf.add(enc_mu, tf.stack(temp_stack))
            #While we are trying to sample some edges, we sample Z from prior
            if sample:
                z = eps
 
	    with tf.variable_scope("Decoder"):
                z_stack = []
                z_stack_weight = []
                z_stack_label = []

                for u in range(n):
                    #'''
                    for j in range(4):
                            # we considered 4 types of atom C, H, O, N,
                            m = np.zeros((1, 4))
                            m[0][j] = 1
                            z_stack_label.append(tf.concat(values=(tf.transpose(z[u]),m), axis = 1)[0])
                    #'''    
                    for v in range(n):
                        z_stack.append(tf.concat(values=(tf.transpose(z[u]), tf.transpose(z[v])), axis = 1)[0])
                        #m = np.zeros((1, self.bin_dim))
                        for j in range(self.bin_dim):
                            #z_stack_weight.append(tf.concat(values=(tf.transpose(z[u]), tf.transpose(z[v]),[[j+1]]), axis = 1)[0])
                            m = np.zeros((1, self.bin_dim))
                            m[0][j] = 1
                            z_stack_weight.append(tf.concat(values=(tf.transpose(z[u]), tf.transpose(z[v]),m), axis = 1)[0])

                dec_hidden = fc_layer(tf.stack(z_stack), 1, activation=tf.nn.softplus, scope = "hidden")
                weight = fc_layer(tf.stack(z_stack_weight), 1, activation=tf.nn.softplus, scope = "marker")
                label = fc_layer(tf.stack(z_stack_label), 1, activation=tf.nn.softplus, scope = "label")

        #return (c_x,enc_mu, enc_sigma, debug_sigma, dec_hidden, prior_mu, prior_sigma, z, weight,[])
        return (c_x,enc_mu, enc_sigma, debug_sigma, dec_hidden, prior_mu, prior_sigma, z, weight, label)

    def call(self,inputs,n,d,k,eps_passed, sample):
            return self.__call__(inputs,n,d,k, eps_passed, sample)
