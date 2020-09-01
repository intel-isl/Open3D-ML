# model settings
model = dict(
    k_n=16,  # KNN,
    num_layers=5,  # Number of layers
    num_points=65536,  # Number of input points
    num_classes=9,  # Number of valid classes
    sub_grid_size=0.06,  # preprocess_parameter
    sub_sampling_ratio=[4, 4, 4, 4, 2],
    num_sub_points=[
        65536 // 4, 65536 // 16, 65536 // 64, 65536 // 256, 65536 // 512
    ],
    d_in=3,
    d_feature=8,
    d_out=[16, 64, 128, 256, 512],
    grid_size=0.06,
    batcher='DefaultBatcher',
    ignored_label_inds=[0],
    ckpt_path='./ml3d/torch/checkpoint/randlanet_parislille3d.pth')

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
    model_name='RandLANet',
    train_sum_dir='train_log',
)

dataset = dict(
    dataset_path='/Users/sanskara/data/Paris_Lille_3D/',
    cache_dir='/Users/sanskara/data/Paris_Lille_3D/cache/',
    prepro_grid_size=0.06,
    num_points=65536,
    test_result_folder='./test',
    class_weights=[
        5181602, 5012952, 6830086, 1311528, 10476365, 946982, 334860, 269353,
        269353
    ],
    ignored_label_inds=[0],
    train_dir='/Users/sanskara/data/Paris_Lille_3D/' + 'training_10_classes/',
    val_files=['Lille2.ply'],
    test_dir='/Users/sanskara/data/Paris_Lille_3D/' + 'test_10_classes/',
)
