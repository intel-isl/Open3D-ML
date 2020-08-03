#coding: future_fstrings
import torch, pickle
import torch.nn as nn
import helper_torch_util
import numpy as np
import logging
import sys

from pprint import pprint
from datetime import datetime
from tqdm import tqdm
from sklearn.neighbors import KDTree
from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import Dataset, IterableDataset, DataLoader, Sampler, BatchSampler

from os.path import exists, join, isfile, dirname, abspath

from ml3d.torch.datasets import SimpleDataset, DefaultBatcher, ConcatBatcher
from ml3d.datasets.semantickitti import DataProcessing

from ml3d.torch.modules.losses import SemSegLoss
from ml3d.torch.modules.metrics import SemSegMetric
from ml3d.torch.utils import make_dir, LogRecord

import yaml

logging.setLogRecordFactory(LogRecord)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(module)s - %(message)s',
)
log = logging.getLogger(__name__)


class SemanticSegmentation():
    def __init__(self, model, dataset, cfg):
        self.model = model
        self.dataset = dataset
        self.cfg = cfg

        make_dir(cfg.main_log_dir)
        cfg.logs_dir = join(cfg.main_log_dir, cfg.model_name)
        make_dir(cfg.logs_dir)

        # dataset.cfg.num_points = model.cfg.num_points

    def run_inference(self, points, device):
        cfg = self.cfg
        model = self.model

        model.to(device)
        model.eval()

        with torch.no_grad():
            inputs = model.preprocess_inference(points, device)
            scores = model(inputs)
            pred = torch.max(scores.squeeze(0), dim=-1).indices
            # pred    = pred.cpu().data.numpy()

        return pred

    def run_test(self, device):
        #self.device = device
        model = self.model
        dataset = self.dataset
        cfg = self.cfg
        model.to(device)
        model.eval()

        timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

        log_file_path = join(cfg.logs_dir, 'log_test_' + timestamp + '.txt')
        log.addHandler(logging.FileHandler(log_file_path))

        test_sampler = dataset.get_sampler(cfg.test_batch_size, 'test')
        test_loader = DataLoader(test_sampler, batch_size=cfg.test_batch_size)
        test_probs = [
            np.zeros(
                shape=[len(l), self.model.cfg.num_classes], dtype=np.float16)
            for l in dataset.possibility
        ]

        self.load_ckpt(model.cfg.ckpt_path, False)
        log.info("Model Loaded from : {}".format(model.cfg.ckpt_path))

        test_smooth = 0.98
        epoch = 0

        log.info("Started testing")

        with torch.no_grad():
            while True:
                for batch_data in tqdm(test_loader, desc='test', leave=False):
                    # loader: point_clout, label
                    inputs = model.preprocess(batch_data, device)
                    result_torch = model(inputs)
                    result_torch = torch.reshape(result_torch,
                                                 (-1, model.cfg.num_classes))

                    m_softmax = nn.Softmax(dim=-1)
                    result_torch = m_softmax(result_torch)
                    stacked_probs = result_torch.cpu().data.numpy()

                    stacked_probs = np.reshape(stacked_probs, [
                        cfg.test_batch_size, model.cfg.num_points,
                        model.cfg.num_classes
                    ])

                    point_inds = inputs['input_inds']
                    cloud_inds = inputs['cloud_inds']

                    for j in range(np.shape(stacked_probs)[0]):
                        probs = stacked_probs[j, :, :]
                        inds = point_inds[j, :]
                        c_i = cloud_inds[j][0]
                        test_probs[c_i][
                            inds] = test_smooth * test_probs[c_i][inds] + (
                                1 - test_smooth) * probs

                new_min = np.min(dataset.min_possibility)
                log.info(f"Epoch {epoch:3d}, end. "
                         f"Min possibility = {new_min:.1f}")

                if np.min(dataset.min_possibility) > 0.5:  # 0.5
                    log.info(f"\nReproject Vote #"
                             f"{int(np.floor(new_min)):d}")
                    dataset.save_test_result(
                        test_probs, str(dataset.cfg.test_split_number))
                    log.info(f"{str(dataset.cfg.test_split_number)}"
                             f" finished")

                    return

                epoch += 1

    def run_train(self, device):
        model = self.model
        model.device = device
        dataset = self.dataset

        cfg = self.cfg
        model.to(device)

        log.info("DEVICE : {}".format(device))
        log.info(model)

        timestamp = datetime.now().strftime('%Y-%m-%d_%H:%M:%S')

        log_file_path = join(cfg.logs_dir, 'log_train_' + timestamp + '.txt')
        log.info("Logging in file : {}".format(log_file_path))
        log.addHandler(logging.FileHandler(log_file_path))

        Loss = SemSegLoss(self, model, dataset, device)
        Metric = SemSegMetric(self, model, dataset, device)

        batcher = self.get_batcher(device)
        train_split = SimpleDataset(
            dataset=dataset.get_split('training'),
            preprocess=model.preprocess,
            transform=model.transform,
            shuffle=True)
        train_loader = DataLoader(
            train_split,
            batch_size=cfg.batch_size,
            shuffle=True,
            collate_fn=batcher.collate_fn)

        
        valid_split = SimpleDataset(
            dataset=dataset.get_split('validation'),
            preprocess=model.preprocess,
            transform=model.transform,
            shuffle=True)
        valid_loader = DataLoader(
            train_split,
            batch_size=cfg.val_batch_size,
            shuffle=True,
            collate_fn=batcher.collate_fn)
        

        optimizer = torch.optim.Adam(model.parameters(), lr=cfg.adam_lr)
        scheduler = torch.optim.lr_scheduler.ExponentialLR(
            optimizer, cfg.scheduler_gamma)

        self.optimizer, self.scheduler = optimizer, scheduler

        first_epoch = self.load_ckpt(model.cfg.ckpt_path, True)

        writer = SummaryWriter(join(cfg.logs_dir, cfg.train_sum_dir))

        log.info("Started training")

        for epoch in range(0, cfg.max_epoch + 1):

            print(f'=== EPOCH {epoch:d}/{cfg.max_epoch:d} ===')
            model.train()
            self.losses = []
            self.accs = []
            self.ious = []
            step = 0

            for idx, inputs in enumerate(tqdm(train_loader, 
                                        desc='training')):
                results = model(inputs['data'])
                loss, gt_labels, predict_scores = model.loss(
                    Loss, results, inputs, device)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                acc = Metric.acc(predict_scores, gt_labels)
                iou = Metric.iou(predict_scores, gt_labels)
                self.losses.append(loss.cpu().item())
                self.accs.append(acc)
                self.ious.append(iou)
                step = step + 1
                

            scheduler.step()
            

            # --------------------- validation
            model.eval()
            self.valid_losses = []
            self.valid_accs = []
            self.valid_ious = []
            step = 0
            with torch.no_grad():

                for idx, inputs in enumerate(tqdm(valid_loader, 
                                            desc='validation')):
                    results = model(inputs['data'])
                    loss, gt_labels, predict_scores = model.loss(
                        Loss, results, inputs, device)
                    acc = Metric.acc(predict_scores, gt_labels)
                    iou = Metric.iou(predict_scores, gt_labels)
                    self.valid_losses.append(loss.cpu().item())
                    self.valid_accs.append(acc)
                    self.valid_ious.append(iou)
                    step = step + 1

            self.save_logs(writer, epoch)

            if epoch % cfg.save_ckpt_freq == 0:
                path_ckpt = join(self.cfg.logs_dir, 'checkpoint')
                self.save_ckpt(path_ckpt, epoch)

    def get_batcher(self, device):
        batcher_name = getattr(self.model.cfg, 'batcher')
        if batcher_name == 'DefaultBatcher':
            batcher = DefaultBatcher()
        elif batcher_name == 'ConcatBatcher':
            batcher = ConcatBatcher(device)
        else:
            batcher = None
        return batcher

    def save_logs(self, writer, epoch):
        accs = np.nanmean(np.array(self.accs), axis=0)
        ious = np.nanmean(np.array(self.ious), axis=0)

        valid_accs = np.nanmean(np.array(self.valid_accs), axis=0)
        valid_ious = np.nanmean(np.array(self.valid_ious), axis=0)

        loss_dict = {
            'Training loss': np.mean(self.losses),
            'Validation loss': np.mean(self.valid_losses)
        }
        acc_dicts = [{
            'Training accuracy': acc,
            'Validation accuracy': val_acc
        } for acc, val_acc in zip(accs, valid_accs)]
        iou_dicts = [{
            'Training IoU': iou,
            'Validation IoU': val_iou
        } for iou, val_iou in zip(ious, valid_ious)]

        # send results to tensorboard
        writer.add_scalars('Loss', loss_dict, epoch)

        for i in range(self.model.cfg.num_classes):
            writer.add_scalars(f'Per-class accuracy/{i+1:02d}', acc_dicts[i],
                               epoch)
            writer.add_scalars(f'Per-class IoU/{i+1:02d}', iou_dicts[i], epoch)

        writer.add_scalars('Overall accuracy', acc_dicts[-1], epoch)
        writer.add_scalars('Mean IoU', iou_dicts[-1], epoch)

        log.info(f"loss train: {loss_dict['Training loss']:.3f} "
                 f" eval: {loss_dict['Validation loss']:.3f}")
        log.info(f"acc train: {acc_dicts[-1]['Training accuracy']:.3f} "
                 f" eval: {acc_dicts[-1]['Validation accuracy']:.3f}")
        log.info(f"acc train: {iou_dicts[-1]['Training IoU']:.3f} "
                 f" eval: {iou_dicts[-1]['Validation IoU']:.3f}")

        # print(acc_dicts[-1])

    def load_ckpt(self, ckpt_path, is_train=True):
        if exists(ckpt_path):
            #path = max(list((cfg.ckpt_path).glob('*.pth')))
            log.info(f'Loading checkpoint {ckpt_path}')
            ckpt = torch.load(ckpt_path)
            first_epoch = ckpt['epoch'] + 1
            self.model.load_state_dict(ckpt['model_state_dict'])
            if is_train:
                self.optimizer.load_state_dict(ckpt['optimizer_state_dict'])
                self.scheduler.load_state_dict(ckpt['scheduler_state_dict'])
        else:
            first_epoch = 0
            log.info('No checkpoint')

        return first_epoch

    def save_ckpt(self, path_ckpt, epoch):
        make_dir(path_ckpt)
        torch.save(
            dict(
                epoch=epoch,
                model_state_dict=self.model.state_dict(),
                optimizer_state_dict=self.optimizer.state_dict(),
                scheduler_state_dict=self.scheduler.state_dict()),
            join(path_ckpt, f'ckpt_{epoch:02d}.pth'))
        log.info(f'Epoch {epoch:3d}: save ckpt to {path_ckpt:s}')

    def filter_valid(self, scores, labels, device):
        valid_scores = scores.reshape(-1, self.model.cfg.num_classes)
        valid_labels = labels.reshape(-1).to(device)

        ignored_bool = torch.zeros_like(valid_labels, dtype=torch.bool)
        for ign_label in self.dataset.cfg.ignored_label_inds:
            ignored_bool = torch.logical_or(ignored_bool,
                                            torch.eq(valid_labels, ign_label))

        valid_idx = torch.where(torch.logical_not(ignored_bool))[0].to(device)

        valid_scores = torch.gather(valid_scores, 0,
                                    valid_idx.unsqueeze(-1).expand(
                                        -1, self.model.cfg.num_classes))
        valid_labels = torch.gather(valid_labels, 0, valid_idx)

        # Reduce label values in the range of logit shape
        reducing_list = torch.arange(
            0, self.model.cfg.num_classes, dtype=torch.int64)
        inserted_value = torch.zeros([1], dtype=torch.int64)

        for ign_label in self.dataset.cfg.ignored_label_inds:
            reducing_list = torch.cat([
                reducing_list[:ign_label], inserted_value,
                reducing_list[ign_label:]
            ], 0)
        valid_labels = torch.gather(reducing_list.to(device), 0, valid_labels)

        valid_labels = valid_labels.unsqueeze(0)
        valid_scores = valid_scores.unsqueeze(0).transpose(-2, -1)

        return valid_scores, valid_labels
