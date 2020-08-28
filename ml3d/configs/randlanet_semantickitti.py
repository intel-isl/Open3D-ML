# model settings
model = dict(
    k_n=16,  # KNN,
    num_layers=4,  # Number of layers
    num_points=4096 * 11,  # Number of input points
    num_classes=19,  # Number of valid classes
    ignored_label_inds=[0],
    sub_grid_size=0.06,  # preprocess_parameter
    sub_sampling_ratio=[4, 4, 4, 4],
    num_sub_points=[
        4096 * 11 // 4, 4096 * 11 // 16, 4096 * 11 // 64, 4096 * 11 // 256
    ],
    d_in=3,
    d_feature=8,
    d_out=[16, 64, 128, 256],
    grid_size=0.06,
    training_batcher='DefaultBatcher',
    test_batcher='DefaultBatcher',
    ckpt_path='./ml3d/torch/checkpoint/randlanet_semantickitti.pth')

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
    original_pc_path='./datasets/SemanticKITTI/dataset/sequences',
    dataset_path='./datasets/SemanticKITTI/dataset/sequences',
    cache_dir='./logs/cache',

    use_cache=False,
    test_result_folder='./test',

    training_split      = ['00', '01', '02', '03', '04', '05',
     '06', '07', '09', '10'],
    #training_split=['01'],
    validation_split=['08'],
    #validation_split=['01'],

    test_split=['11', '12', '13', '14', '15', '16', '17', 
                '18', '19', '20', '21'],
    all_split=['00', '01', '02', '03', '04', '05', '06', '07', 
                '09', '08', '10', '11', '12', '13', '14', '15', 
                '16', '17', '18', '19', '20', '21'],
    test_split_number=11,
    class_weights=[
        55437630, 320797, 541736, 2578735, 3274484, 552662, 184064, 78858,
        240942562, 17294618, 170599734, 6369672, 230413074, 101130274,
        476491114, 9833174, 129609852, 4506626, 1168181
    ],
)
