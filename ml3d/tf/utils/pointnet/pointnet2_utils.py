import tensorflow as tf
from tensorflow.python.framework import ops
from typing import Tuple

import open3d

import open3d.ml.tf.ops as ml_ops


def furthest_point_sample(xyz, npoint):
    """
    Uses iterative furthest point sampling to select a set of npoint features that have the largest
    minimum distance
    :param xyz: (B, N, 3) where N > npoint
    :param npoint: int, number of features in the sampled set
    :return:tensor containing the set
    """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    output = ml_ops.furthest_point_sampling(xyz, npoint)
    return output


ops.NoGradient('Open3DFurthestPointSampling')


def gather_operation(features, idx):
    """
        :param features: (B, C, N)
        :param idx: (B, npoint) index tensor of the features to gather
        :return:
            output: (B, C, npoint)
        """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    output = ml_ops.gather_points(features, idx)

    return output


@tf.RegisterGradient('Open3DGatherPoints')
def _gather_operation_grad(op, out_g):
    inp = op.inputs[0]
    idx = op.inputs[1]
    C, N = inp.shape[1:3]
    return [ml_ops.gather_points_grad(out_g, idx, C, N), None]


def three_nn_gpu(query_pts, data_pts):
    """
    Find the three nearest neighbors of query_pts in data_pts
    :param query_pts: (B, N, 3)
    :param data_pts: (B, M, 3)
    :return:
        dist: (B, N, 3) l2 distance to the three nearest neighbors
        idx: (B, N, 3) index of 3 nearest neighbors
    """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    dist2, idx = ml_ops.three_nn(query_pts, data_pts)
    return tf.sqrt(dist2), idx


ops.NoGradient("Open3DTreeNN")


def three_interpolate_gpu(features, idx, weight):
    """
        Performs weight linear interpolation on 3 features
        :param features: (B, C, M) Features descriptors to be interpolated from
        :param idx: (B, n, 3) three nearest neighbors of the target features in features
        :param weight: (B, n, 3) weights
        :return:
            output: (B, C, N) tensor of the interpolated features
        """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    output = ml_ops.three_interpolate(features, idx, weight)
    return output


@tf.RegisterGradient("Open3DThreeInterpolate")
def _tree_interpolate_gradient(op, grad_out):
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    features = op.inputs[0]
    idx = op.inputs[1]
    weight = op.inputs[2]

    m = features.shape[2]

    grad_features = ml_ops.three_interpolate_grad(grad_out, idx, weight, m)
    return grad_features, None, None


def grouping_operation(features, idx):
    """
    :param features: (B, C, N) tensor of features to group
    :param idx: (B, npoint, nsample) tensor containing the indicies of features to group with
    :return:
        output: (B, C, npoint, nsample) tensor
    """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    output = ml_ops.group_points(features, idx)
    return output


@tf.RegisterGradient("Open3DGroupPoints")
def _grouping_operation_gradient(op, grad_out):
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    features, idx = op.inputs

    N = features.shape[2]

    grad_features = ml_ops.group_points_grad(grad_out, idx, N)
    return grad_features, None


def ball_query_gpu(radius, nsample, xyz, new_xyz):
    """
        :param radius: float, radius of the balls
        :param nsample: int, maximum number of features in the balls
        :param xyz: (B, N, 3) xyz coordinates of the features
        :param new_xyz: (B, npoint, 3) centers of the ball query
        :return:
            idx: (B, npoint, nsample) tensor with the indicies of the features that form the query balls
        """
    if not open3d.core.cuda.device_count() > 0:
        raise NotImplementedError

    idx = ml_ops.ball_query(xyz, new_xyz, radius, nsample)
    return idx


ops.NoGradient("Open3DBallQuery")


class QueryAndGroup(tf.keras.layers.Layer):

    def __init__(self, radius: float, nsample: int, use_xyz: bool = True):
        """
        :param radius: float, radius of ball
        :param nsample: int, maximum number of features to gather in the ball
        :param use_xyz:
        """
        super().__init__()
        self.radius, self.nsample, self.use_xyz = radius, nsample, use_xyz

    def call(self, xyz, new_xyz, features=None):
        """
        :param xyz: (B, N, 3) xyz coordinates of the features
        :param new_xyz: (B, npoint, 3) centroids
        :param features: (B, C, N) descriptors of the features
        :return:
            new_features: (B, 3 + C, npoint, nsample)
        """
        if not open3d.core.cuda.device_count() > 0:
            raise NotImplementedError

        idx = ball_query_gpu(self.radius, self.nsample, xyz, new_xyz)
        xyz_trans = tf.transpose(xyz, (0, 2, 1))
        grouped_xyz = grouping_operation(xyz_trans,
                                         idx)  # (B, 3, npoint, nsample)
        grouped_xyz -= tf.expand_dims(tf.transpose(new_xyz, (0, 2, 1)), axis=-1)

        if features is not None:
            grouped_features = grouping_operation(features, idx)
            if self.use_xyz:
                new_features = tf.concat([grouped_xyz, grouped_features],
                                         axis=1)  # (B, C + 3, npoint, nsample)
            else:
                new_features = grouped_features
        else:
            assert self.use_xyz, "Cannot have not features and not use xyz as a feature!"
            new_features = grouped_xyz

        return new_features


class GroupAll(tf.keras.layers.Layer):

    def __init__(self, use_xyz: bool = True):
        super().__init__()
        self.use_xyz = use_xyz

    def call(self, xyz, new_xyz, features=None):
        """
        :param xyz: (B, N, 3) xyz coordinates of the features
        :param new_xyz: ignored
        :param features: (B, C, N) descriptors of the features
        :return:
            new_features: (B, C + 3, 1, N)
        """
        if not open3d.core.cuda.device_count() > 0:
            raise NotImplementedError

        grouped_xyz = tf.expand_dims(tf.transpose(xyz, (0, 2, 1)), axis=2)
        if features is not None:
            grouped_features = tf.expand_dims(features, axis=2)
            if self.use_xyz:
                new_features = tf.concat([grouped_xyz, grouped_features],
                                         axis=1)  # (B, 3 + C, 1, N)
            else:
                new_features = grouped_features
        else:
            new_features = grouped_xyz

        return new_features
