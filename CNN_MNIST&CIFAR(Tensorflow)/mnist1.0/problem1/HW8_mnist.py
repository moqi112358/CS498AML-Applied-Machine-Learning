from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import argparse
import sys
import numpy as np
from tensorflow.examples.tutorials.mnist import input_data
import tensorflow as tf
FLAGS = None
  
def train():
	f = open('acc.txt', 'w')
	# Import data
	mnist = input_data.read_data_sets(FLAGS.data_dir,one_hot=True,fake_data=FLAGS.FakeData)
	sess = tf.InteractiveSession()
	def weight_variable(shape):
		initial = tf.truncated_normal(shape, stddev=0.1)
		return tf.Variable(initial)

	def bias_variable(shape):
		initial = tf.constant(0.1, shape=shape)
		return tf.Variable(initial)

	def variable_summaries(var,name):
		with tf.name_scope('summaries'):
			mean = tf.reduce_mean(var)
			tf.summary.scalar('mean/' + name, mean)
			with tf.name_scope('stddev'):
				stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
			tf.summary.scalar('stddev/' + name, stddev)
			tf.summary.scalar('max/' + name, tf.reduce_max(var))
			tf.summary.scalar('min/' + name, tf.reduce_min(var))
			tf.summary.histogram(name, var)

	def nn_layer(input_tensor, input_dim, output_dim, layer_name, act=tf.nn.relu):
    # Adding a name scope ensures logical grouping of the layers in the graph.
		with tf.name_scope(layer_name):
			# This Variable will hold the state of the weights for the layer
			with tf.name_scope('weights'):
				weights = weight_variable([input_dim, output_dim])
				variable_summaries(weights,layer_name + '/weights')
			with tf.name_scope('biases'):
				biases = bias_variable([output_dim])
				variable_summaries(biases,layer_name + '/biases')
			with tf.name_scope('Wx_plus_b'):
				preactivate = tf.matmul(input_tensor, weights) + biases
				tf.summary.histogram(layer_name + 'pre_activations', preactivate)
			activations = act(preactivate, name='activation')
			tf.summary.histogram(layer_name + 'activations', activations)
			return activations

	def feed_dict(train):
		if train or FLAGS.FakeData:
			xs, ys = mnist.train.next_batch(100, fake_data=FLAGS.FakeData)
			k = FLAGS.dropout
		else:
			xs, ys = mnist.test.images, mnist.test.labels
			k = 1.0
		return {x: xs, y_: ys, keep_prob: k}


	# Input placeholders
	with tf.name_scope('input'):
		x = tf.placeholder(tf.float32, [None, 784], name='x-input')
		y_ = tf.placeholder(tf.float32, [None, 10], name='y-input')

	with tf.name_scope('input_reshape'):
		image_shaped_input = tf.reshape(x, [-1, 28, 28, 1])
		tf.summary.image('input', image_shaped_input, 10)

	hidden1 = nn_layer(x, 784, 500, 'layer1')
	with tf.name_scope('dropout'):
		keep_prob = tf.placeholder(tf.float32)
		tf.summary.scalar('dropout_keep_probability', keep_prob)
		dropped = tf.nn.dropout(hidden1, keep_prob)

	
	y = nn_layer(dropped, 500, 10, 'layer2', act=tf.nn.softmax)

	with tf.name_scope('cross_entropy'):
		diff = tf.nn.softmax_cross_entropy_with_logits(labels=y_, logits=y)
		with tf.name_scope('total'):
			cross_entropy = tf.reduce_mean(diff)
		tf.summary.scalar('cross_entropy', cross_entropy)

	with tf.name_scope('train'):
		train_step = tf.train.AdamOptimizer(FLAGS.lambda_).minimize(cross_entropy)

	with tf.name_scope('accuracy'):
		with tf.name_scope('correct_prediction'):
			correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(y_, 1))
		with tf.name_scope('accuracy'):
			accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
	tf.summary.scalar('accuracy', accuracy)

  # Merge all the summaries and write them out to
  # /tmp/tensorflow/mnist/logs/mnist_with_summaries (by default)
	merged = tf.summary.merge_all()
	train_writer = tf.summary.FileWriter(FLAGS.log_dir + '/train', sess.graph)
	test_writer = tf.summary.FileWriter(FLAGS.log_dir + '/test')
	tf.global_variables_initializer().run()
	train_d = np.zeros((784))
	test_d = np.zeros((10))
	tr_acc_list = []
	for i in range(FLAGS.max_step):
		if i % 100 == 0:
			summary, acc = sess.run([merged, accuracy], feed_dict=feed_dict(False))
			test_writer.add_summary(summary, i)
			if i != 0:
				s,tr_acc = sess.run([merged,accuracy],feed_dict={x:train_d[1:,],y_:test_d[1:,],keep_prob: 1.0})
				f.write('Step: %s Train Accuracy: %s Test Accuracy: %s\n' % (i, tr_acc, acc))
				print('Step: %s Train Accuracy: %s Test Accuracy: %s' % (i, tr_acc, acc))
				tr_acc_list.append(acc)
			else:
				f.write('Step: %s Test Accuracy: %s\n' % (i, acc))
				print('Step: %s Test Accuracy: %s' % (i, acc))
			train_d = np.zeros((784))
			test_d = np.zeros((10))
		else: 
			fd_train = feed_dict(True)
			summary, _ = sess.run([merged, train_step], feed_dict=fd_train)
			train_writer.add_summary(summary, i)
			train_d = np.vstack((train_d,list(fd_train.values())[0]))
			test_d = np.vstack((test_d,list(fd_train.values())[1]))
	f.write('\n Average test accuracy: %s' % (np.mean(tr_acc_list)))
	f.write('\n Max test accuracy: %s' % (np.amax(tr_acc_list)))
	f.close()

def main(_):
	if tf.gfile.Exists(FLAGS.log_dir):
		tf.gfile.DeleteRecursively(FLAGS.log_dir)
	tf.gfile.MakeDirs(FLAGS.log_dir)
	train()
  
if __name__ == '__main__':
	flags = tf.app.flags
	FLAGS = flags.FLAGS
	flags.DEFINE_boolean('FakeData', False, 'If true, uses fake data for unit testing.')
	flags.DEFINE_integer('max_step', 2001, 'Number of steps to run trainer.') ##
	flags.DEFINE_float('lambda_', 0.002, 'Initial learning rate.')
	flags.DEFINE_float('dropout', 0.9, 'Keep probability for training dropout.')
	flags.DEFINE_string('data_dir', '/home/huaminz2/cs498/hw8/mnist/problem1/input_data', 'Directory for storing data')
	flags.DEFINE_string('log_dir', '/home/huaminz2/cs498/hw8/mnist/problem1/mnist_with_summaries', 'Summaries log directory')
	#parser.add_argument('--fake_data', nargs='?', const=True, type=bool,default=False,help='If true, uses fake data for unit testing.')
	#parser.add_argument('--max_steps', type=int, default=1000,help='Number of steps to run trainer.')
	#parser.add_argument('--learning_rate', type=float, default=0.001,help='Initial learning rate')
	#parser.add_argument('--dropout',type=float, default=0.9,help='Keep probability for training dropout.')
	#parser.add_argument('--data_dir',type=str,default='/tmp/tensorflow/mnist/input_data',help='Directory for storing input data')
	#parser.add_argument('--log_dir',type=str,default='/tmp/tensorflow/mnist/logs/mnist_with_summaries',help='Summaries log directory')
	#FLAGS, unparsed = parser.parse_known_args()
	tf.app.run()
			
	
 