import torch
import torch.nn as nn
import numpy as np


def filter_valid_label(scores, labels, num_classes, ignored_label_inds,
                       device):
    """filter out invalid points"""
    valid_scores = scores.reshape(-1, num_classes)
    valid_labels = labels.reshape(-1).to(device)

    ignored_bool = torch.zeros_like(valid_labels, dtype=torch.bool)
    for ign_label in ignored_label_inds:
        ignored_bool = torch.logical_or(ignored_bool,
                                        torch.eq(valid_labels, ign_label))

    valid_idx = torch.where(torch.logical_not(ignored_bool))[0].to(device)

    valid_scores = torch.gather(valid_scores, 0,
                                valid_idx.unsqueeze(-1).expand(
                                    -1, num_classes))
    valid_labels = torch.gather(valid_labels, 0, valid_idx)

    # Reduce label values in the range of logit shape
    reducing_list = torch.arange(0, num_classes, dtype=torch.int64)
    inserted_value = torch.zeros([1], dtype=torch.int64)

    for ign_label in ignored_label_inds:

        reducing_list = torch.cat([
            reducing_list[:ign_label], inserted_value,
            reducing_list[ign_label:]
        ], 0)
    valid_labels = torch.gather(reducing_list.to(device), 0, valid_labels)

    valid_labels = valid_labels.unsqueeze(0)
    valid_scores = valid_scores.unsqueeze(0).transpose(-2, -1)

    return valid_scores, valid_labels


class SemSegLoss(object):
    """Loss functions for semantic segmentation"""

    def __init__(self, pipeline, model, dataset, device):
        super(SemSegLoss, self).__init__()
        # weighted_CrossEntropyLoss
        n_samples = torch.tensor(
            dataset.cfg.class_weights, dtype=torch.float, device=device)
        ratio_samples = n_samples / n_samples.sum()
        weights = 1 / (ratio_samples + 0.02)
        
        self.weighted_CrossEntropyLoss = nn.CrossEntropyLoss(weight=weights)
