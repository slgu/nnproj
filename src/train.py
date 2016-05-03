from renet import *
def test_renet(**kwargs):
    param = {
        'lr': 0.097,
        'verbose': True,
        'n_epochs':200,
        'batch_size':200,
        'ds_rate':5,
        'renet_d':5,
        'w':32,
        'h':32,
        'c':3,
        'patch_size':4,
        'hidden_num':1,
        'hidden_unit':200
    }
    param_diff = set(kwargs.keys()) - set(param.keys())
    if param_diff:
        raise KeyError("invalid arguments:" + str(tuple(param_diff)))
    param.update(kwargs)
    if param['verbose']:
        for k,v in param.items():
            print("%s: %s" % (k,v))
    learning_rate = param['lr']
    batch_size = param['batch_size']
    ds_rate = param['ds_rate']
    renet_d = param['renet_d']
    hidden_unit = param['hidden_unit']
    hidden_layer_num = param['hidden_num']
    wp = param['patch_size']
    hp = param['patch_size']
    w = param['w']
    h = param['h']
    c = param['c']
    rng = numpy.random.RandomState(23455)

    datasets = load_cifar_data(ds_rate=5)
    train_set_x, train_set_y = datasets[0]
    valid_set_x, valid_set_y = datasets[1]
    test_set_x, test_set_y = datasets[2]

    # compute number of minibatches for training, validation and testing
    n_train_batches = train_set_x.get_value(borrow=True).shape[0]
    n_valid_batches = valid_set_x.get_value(borrow=True).shape[0]
    n_test_batches = test_set_x.get_value(borrow=True).shape[0]
    n_train_batches //= batch_size
    n_valid_batches //= batch_size
    n_test_batches //= batch_size

    # allocate symbolic variables for the data
    index = T.lscalar()  # index to a [mini]batch

    x = T.matrix('x')   # the data is presented as rasterized images
    y = T.ivector('y')  # the labels are presented as 1D vector of
                        # [int] labels

    # BUILD ACTUAL MODEL #
    ######################
    print('... building the model')

    # Reshape matrix of rasterized images of shape (batch_size, 3 * 32 * 32)
    # to a 4D tensor, compatible with our LeNetConvPoolLayer
    layer0_input = x.reshape((batch_size, w, h, c))
    layer0 = ReNet(
        input=layer0_input,
        batch_size=batch_size,
        w=w,
        h=h,
        c=c,
        wp=wp,
        hp=hp,
        d=renet_d
    )

    '''
    layer1 = ReNet(
        input=layer0.output,
        batch_size=batch_size,
        w=w/wp,
        h=h/hp,
        c=2*renet_d,
        wp=wp,
        hp=hp,
        d=renet_d
    )
    '''
    layer2_input = layer0.output.flatten(2)

    layer2 = myMLP(
        rng,
        input=layer2_input,
        n_in=((renet_d * 2) * (w * h / wp / hp)),
        n_hidden=hidden_unit,
        n_out=10,
        n_hiddenLayers=hidden_layer_num,
        activation=T.tanh
    )

    cost = layer2.negative_log_likelihood(y)

    print("cost done")
    # create a function to compute the mistakes that are made by the model
    test_model = theano.function(
        [index],
        layer2.errors(y),
        givens={
            x: test_set_x[index * batch_size: (index + 1) * batch_size],
            y: test_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )
    print("test model done")

    validate_model = theano.function(
        [index],
        layer2.errors(y),
        givens={
            x: valid_set_x[index * batch_size: (index + 1) * batch_size],
            y: valid_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )
    print("test valid model done")

    params = layer2.params + layer0.params

    # create a list of gradients for all model parameters
    grads = T.grad(cost, params)

    # train_model is a function that updates the model parameters by
    # SGD Since this model has many parameters, it would be tedious to
    # manually create an update rule for each model parameter. We thus
    # create the updates list by automatically looping over all
    # (params[i], grads[i]) pairs.
    updates = [
        (param_i, param_i - learning_rate * grad_i)
        for param_i, grad_i in zip(params, grads)
    ]
    print("update done")

    train_model = theano.function(
        [index],
        cost,
        updates=updates,
        givens={
            x: train_set_x[index * batch_size: (index + 1) * batch_size],
            y: train_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )

    print("train model done")
    ###############
    # TRAIN MODEL #
    ###############
    print('... training')

    train_nn(train_model, validate_model, test_model,
        n_train_batches, n_valid_batches, n_test_batches, param['n_epochs'], param['verbose'])


if __name__ == '__main__':
    test_renet(lr=0.1)
