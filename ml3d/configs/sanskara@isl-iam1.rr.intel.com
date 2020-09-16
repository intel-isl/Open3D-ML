dataset:
  name: S3DIS
  dataset_path: # path/to/your/dataset
  cache_dir: ./logs/cache
  class_weights: [3370714, 2856755, 4919229, 318158, 375640, 
  478001, 974733, 650464, 791496, 88727, 1284130, 229758, 2272837]
  ignored_label_inds: []
  num_points: 40960
  prepro_grid_size: 0.04
  test_area_idx: 3
  test_result_folder: ./test
  use_cache: false
model:
  name: KPFCNN
  KP_extent: 1.2
  KP_influence: linear
  aggregation_mode: sum
  architecture:
  - simple
  - resnetb
  - resnetb_strided
  - resnetb
  - resnetb
  - resnetb_strided
  - resnetb
  - resnetb
  - resnetb_strided
  - resnetb
  - resnetb
  - resnetb_strided
  - resnetb
  - nearest_upsample
  - unary
  - nearest_upsample
  - unary
  - nearest_upsample
  - unary
  - nearest_upsample
  - unary
  augment_color: 0.8
  augment_noise: 0.001
  augment_rotation: vertical
  augment_scale_anisotropic: true
  augment_scale_max: 1.2
  augment_scale_min: 0.8
  augment_symmetries:
  - true
  - false
  - false
  batch_limit: 50000
  batch_norm_momentum: 0.02
  batch_num: 8
  batcher: ConcatBatcher
  ckpt_path: # path/to/your/checkpoint
  class_w: []
  conv_radius: 2.5
  dataset_task: ''
  deform_fitting_mode: point2point
  deform_fitting_power: 1.0
  deform_radius: 6.0
  first_features_dim: 128
  first_subsampling_dl: 0.03
  fixed_kernel_points: center
  ign_lbls:
  - 0
  ignored_label_inds:
  - 0
  in_features_dim: 2
  in_points_dim: 3
  in_radius: 1.5
  input_threads: 10
  lbl_values: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
  max_in_points: 20000
  max_val_points: 100000
  modulated: false
  n_frames: 1
  num_classes: 13
  num_kernel_points: 15
  num_layers: 5
  repulse_extent: 1.2
  use_batch_norm: true
  val_batch_num: 8
  val_radius: 4.0
pipeline:
  name: SemanticSegmentation
  adam_lr: 0.01
  batch_size: 4
  checkpoint_gap: 50
  deform_lr_factor: 0.1
  epoch_steps: 500
  grad_clip_norm: 100.0
  learning_rate: 0.01
  lr_decays: 0.98477
  main_log_dir: ./logs
  max_epoch: 800
  momentum: 0.98
  save_ckpt_freq: 10
  saving: true
  saving_path: null
  scheduler_gamma: 0.98477
  test_batch_size: 4
  train_sum_dir: train_log
  val_batch_size: 4
  validation_size: 200
  weight_decay: 0.001
