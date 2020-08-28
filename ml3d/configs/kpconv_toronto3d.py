# model settings
model = dict(
    ign_lbls=[0],
    lbl_values=[0, 1, 2, 3, 4, 5, 6, 7, 8],
    num_classes=8,  # Number of valid classes
    ignored_label_inds=[0],
    # Dataset name
    dataset='SemanticKitti',
    ckpt_path='./ml3d/torch/checkpoint/kpconv_semantickitti.pth',

    # Type of task performed on this dataset (also overwritten)
    dataset_task='',

    # Number of CPU threads for the input pipeline
    input_threads=10,
    batcher='ConcatBatcher',

    # Density of neighborhoods for deformable convs (which need bigger radiuses). For normal conv we use KP_extent
    density_parameter=5.0,

    #########################
    # Architecture definition
    #########################

    # Define layers
    architecture=[
        'simple', 'resnetb', 'resnetb_strided', 'resnetb', 'resnetb_strided',
        'resnetb', 'resnetb_strided', 'resnetb', 'resnetb_strided', 'resnetb',
        'nearest_upsample', 'unary', 'nearest_upsample', 'unary',
        'nearest_upsample', 'unary', 'nearest_upsample', 'unary'
    ],

    ###################
    # KPConv parameters
    ###################

    # Radius of the input sphere
    in_radius=2.0,
    val_radius=2.0,
    n_frames=1,
    max_in_points=100000,
    max_val_points=100000,

    # Number of batch
    batch_num=8,
    val_batch_num=8,

    # Number of steps per epochs
    epoch_steps=500,

    # Number of kernel points
    num_kernel_points=15,

    # Size of the first subsampling grid in meter
    first_subsampling_dl=0.04,

    # Radius of convolution in "number grid cell". (2.5 is the standard value)
    conv_radius=2.5,

    # Radius of deformable convolution in "number grid cell". Larger so that deformed kernel can spread out
    deform_radius=6.0,

    # Radius of the area of influence of each kernel point in "number grid cell". (1.0 is the standard value)
    KP_extent=1.0,

    # Behavior of convolutions in ('constant', 'linear', 'gaussian')
    KP_influence='linear',

    # Aggregation function of KPConv in ('closest', 'sum')
    aggregation_mode='sum',

    # Choice of input features
    first_features_dim=128,
    in_features_dim=5,

    # Can the network learn modulations
    modulated=False,

    # Batch normalization parameters
    use_batch_norm=True,
    batch_norm_momentum=0.02,

    # Deformable offset loss
    # 'point2point' fitting geometry by penalizing distance from deform point to input points
    # 'point2plane' fitting geometry by penalizing distance from deform point to input point triplet (not implemented)
    deform_fitting_mode='point2point',
    deform_fitting_power=1.0,  # Multiplier for the fitting/repulsive loss
    deform_lr_factor=
    0.1,  # Multiplier for learning rate applied to the deformations
    repulse_extent=1.2,  # Distance of repulsion for deformed kernel points

    #####################
    # Training parameters
    #####################

    # Maximal number of epochs
    max_epoch=800,

    # Learning rate management
    learning_rate=1e-2,
    momentum=0.98,
    lr_decays={i: 0.1**(1 / 150)
               for i in range(1, 800)},
    grad_clip_norm=100.0,

    # Number of validation examples per epoch
    validation_size=200,

    # Number of epoch between each checkpoint
    checkpoint_gap=50,

    # Augmentations
    augment_scale_anisotropic=True,
    augment_symmetries=[True, False, False],
    augment_rotation='vertical',
    augment_scale_min=0.8,
    augment_scale_max=1.2,
    augment_noise=0.001,
    augment_color=0.8,

    # Choose weights for class (used in segmentation loss). Empty list for no weights
    # class proportion for R=10.0 and dl=0.08 (first is unlabeled)
    # 19.1 48.9 0.5  1.1  5.6  3.6  0.7  0.6  0.9 193.2 17.7 127.4 6.7 132.3 68.4 283.8 7.0 78.5 3.3 0.8
    #
    #

    # sqrt(Inverse of proportion * 100)
    # class_w = [1.430, 14.142, 9.535, 4.226, 5.270, 11.952, 12.910, 10.541, 0.719,
    #            2.377, 0.886, 3.863, 0.869, 1.209, 0.594, 3.780, 1.129, 5.505, 11.180]

    # sqrt(Inverse of proportion * 100)  capped (0.5 < X < 5)
    # class_w = [1.430, 5.000, 5.000, 4.226, 5.000, 5.000, 5.000, 5.000, 0.719, 2.377,
    #            0.886, 3.863, 0.869, 1.209, 0.594, 3.780, 1.129, 5.000, 5.000]

    # Do we nee to save convergence
    saving=True,
    saving_path=None,

    # Dimension of input points
    in_points_dim=3,

    # Fixed points in the kernel : 'none', 'center' or 'verticals'
    fixed_kernel_points='center',

    # Choose weights for class (used in segmentation loss). Empty list for no weights
    class_w=[],
    num_layers=5,
)

pipeline = dict(
    batch_size=1,
    val_batch_size=1,
    test_batch_size=1,
    max_epoch=100,  # maximum epoch during training
    learning_rate=1e-2,  # initial learning rate
    #lr_decays           = {0.95 for i in range(0, 500)},
    save_ckpt_freq=20,
    adam_lr=1e-2,
    scheduler_gamma=0.95,

    # logs
    main_log_dir='./logs',
    model_name='KPConv',
    train_sum_dir='train_log',
)

dataset = dict(
    dataset_path='/Users/sanskara/data/Toronto_3D/',
    cache_dir='/Users/sanskara/data/Toronto_3D/cache/',
    use_cache=True,
    prepro_grid_size=0.06,
    num_points=65536,
    test_result_folder='./test',
    class_weights=[
        5181602, 5012952, 6830086, 1311528, 10476365, 946982, 334860, 269353
    ],
    ignored_label_inds=[0],
    train_files=['L001.ply', 'L003.ply', 'L004.ply'],
    val_files=['L002.ply'],
    test_files=['L002.ply'],
)
