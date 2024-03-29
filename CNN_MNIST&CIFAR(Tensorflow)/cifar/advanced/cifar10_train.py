# Copyright 2015 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""A binary to train CIFAR-10 using a single GPU.

Accuracy:
cifar10_train.py achieves ~86% accuracy after 100K steps (256 epochs of
data) as judged by cifar10_eval.py.

Speed: With batch_size 128.

System        | Step Time (sec/batch)  |     Accuracy
------------------------------------------------------------------
1 Tesla K20m  | 0.35-0.60              | ~86% at 60K steps  (5 hours)
1 Tesla K40m  | 0.25-0.35              | ~86% at 100K steps (4 hours)

Usage:
Please see the tutorial and website for how to download the CIFAR-10
data set, compile the program and train the model.

http://tensorflow.org/tutorials/deep_cnn/
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import numpy as np
from datetime import datetime
import time
import os.path
import tensorflow as tf
import numpy as np
from six.moves import xrange
import cifar10
import os
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"  # see issue #152
os.environ["CUDA_VISIBLE_DEVICES"] = "1" 

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_string('train_dir', '/home/huaminz2/cs498/hw8/cifar10/advanced/cifar10_train',
                           """Directory where to write event logs """
                           """and checkpoint.""")
tf.app.flags.DEFINE_integer('max_steps', 70001,
                            """Number of batches to run.""")
tf.app.flags.DEFINE_boolean('log_device_placement', False,
                            """Whether to log device placement.""")
tf.app.flags.DEFINE_integer('log_frequency', 100,
                            """How often to log results to the console.""")

def acc(logits, labels):
  # Calculate the average cross entropy loss across the batch.
  labels = tf.cast(labels, tf.int64)

  # find which images the model correctly predicted 
  correct_prediction = tf.equal(tf.argmax(logits,1), labels)

  accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32), name='accuracy')

  tf.add_to_collection('accuracy', accuracy)

  return tf.add_n(tf.get_collection('accuracy'), name='accuracy')

def train():
  """Train CIFAR-10 for a number of steps."""
  with tf.Graph().as_default():
    global_step = tf.Variable(0, trainable=False)

    # Get images and labels for CIFAR-10.
    images, labels = cifar10.distorted_inputs()

    # Build a Graph that computes the logits predictions from the
    # inference model.
    logits = cifar10.inference(images)

    # Calculate loss.
    loss = cifar10.loss(logits, labels)
    
    #Calculate accuracy
    accuracy = acc(logits, labels)
    
    # Build a Graph that trains the model with one batch of examples and
    # updates the model parameters.
    train_op = cifar10.train(loss, global_step)

    # Create a saver.
    saver = tf.train.Saver(tf.all_variables())

    # Build the summary operation based on the TF collection of Summaries.
    summary_op = tf.summary.merge_all()

    # Build an initialization operation to run below.
    init = tf.global_variables_initializer()

    # Start running operations on the Graph.
    sess = tf.Session(config=tf.ConfigProto(
        log_device_placement=FLAGS.log_device_placement))
    sess.run(init)

    # Start the queue runners.
    tf.train.start_queue_runners(sess=sess)

    summary_writer = tf.summary.FileWriter(FLAGS.train_dir, sess.graph)
    tr_acc_list = []
    for step in xrange(FLAGS.max_steps):
      start_time = time.time()
      _, loss_value,tr_acc = sess.run([train_op, loss, accuracy])
      duration = time.time() - start_time
      assert not np.isnan(loss_value), 'Model diverged with loss = NaN'

      if step % 100 == 0:
        tr_acc_list.append(tr_acc)
        num_examples_per_step = FLAGS.batch_size
        examples_per_sec = num_examples_per_step / duration
        sec_per_batch = float(duration)
        f = open('train.txt','a')
        format_str = ('%s: step %d, loss = %.2f, accuracy = %.2f (%.1f examples/sec; %.3f '
                      'sec/batch)\n')
        f.write(format_str % (datetime.now(), step, loss_value, tr_acc, examples_per_sec, sec_per_batch))
        f.close()
        summary = tf.Summary()
        summary.ParseFromString(sess.run(summary_op))
        summary.value.add(tag='accuracy', simple_value=tr_acc)
        summary_writer.add_summary(summary, step)

      # Save the model checkpoint periodically.
      if step % 100 == 0:
        checkflag = open('check','w+')
        checkflag.write('1')
        checkflag.close()
        checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
        saver.save(sess, checkpoint_path, global_step=step)
      if (step + 1) == FLAGS.max_steps:
        checkflag = open('check','w+')
        checkflag.write('2')
        checkflag.close()
        checkpoint_path = os.path.join(FLAGS.train_dir, 'model.ckpt')
        saver.save(sess, checkpoint_path, global_step=step)
        f = open('train.txt','a')
        f.write('\n Average train accuracy: %s' % (np.mean(tr_acc_list)))
        f.write('\n Max train accuracy: %s\n' % (np.amax(tr_acc_list)))
        f.close()



def main(argv=None):  # pylint: disable=unused-argument
  cifar10.maybe_download_and_extract()
  checkflag = open('check','w+')
  checkflag.write('0')
  checkflag.close()
  if tf.gfile.Exists(FLAGS.train_dir):
    tf.gfile.DeleteRecursively(FLAGS.train_dir)
  tf.gfile.MakeDirs(FLAGS.train_dir) 
  train()


if __name__ == '__main__':
  tf.app.run()
