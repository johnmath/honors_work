from scipy.stats import norm 
import torch
from math import ceil
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
import torch.optim as optim
import torchvision
import torch.nn.functional as F
import numpy as np
import matplotlib.pyplot as plt

# TODO: Create an adaptive algorithm to generate the param_counts 
# TODO: Detect the interpolation threshold using training loss ( < epsilon??)

def approx_sigma(mu, max_params):
    """Approximates standard deviation of a normal distribution given 
    the maximum value and mean. In this context, the desired "interpolation 
    threshold" will be the mean, and the desired maximum number of parameters will
    be the maximum value. Using this, we can sample parameter sizes from a normal
    distribution to avoid the computational cost that comes with training over all 
    parameter sizes in some range
    
    The standard deviation is calculated using the fact that 99.7% of the elements
    in a normal distribution fall within 3*sigma of the mean. So, we can use this
    to approximate the maximum value using max = mean - 3*sigma. Therefore, a rough
    approximate for the standard deviation would be sigma = (max - mean)/3.
    
    ...
    Parameters
    ----------
    mu : int
        The chosen value for the interpolation threshold
    max_params : int
        The desired maximum number of parameters to train up to. 
        The meaning of this will vary depending on the model and
        the dataset. 
        (Ex. The value max_params for an MLP training on MNIST would 
        mean max_params * 10^3 parameters will be the maximum number of 
        parameters)
        
        
    Returns
    -------
    std : float
        Standard deviation of a normal distribution
    """
    
    return (max_params - mu)/3


def get_midpoints(x):
    """Returns an array that contains all the midpoints of consecutive
    values of the original array
    
    ...
    Parameters
    ----------
    x : np.array
        The x axis
    
    Returns
    -------
    midpoints : np.array
        Array of midpoints of consecutve values in the original array
    """
    
    return (x[1:] + x[:-1])/2

    
def derivative(x, y):
    """Computes the discrete derivative of a function given values 
    for x and y or f(x)
    
    ...
    Parameters
    ----------
    x : np.array
        The x axis
    y : np.array
        The y axis
        
        
    Returns
    -------
    midpoints : np.array
        The corresponding x axis for y' or f'(x)
    dy : np.array
        The discrete derivative of y or f(x) with respect to x
    """
    
    if type(x) != np.ndarray:
        x = np.array(x)
        
    if type(y) != np.ndarray:
        y = np.array(y)
    
    assert len(x) == len(y)
    return get_midpoints(x), np.diff(y)/np.diff(x)


def get_next_param_count(param_counts, losses, past_dd=False, alpha=2):
    """Predicts the next paramter count given a list of 
    prior parameter counts and losses. This works by fitting
    a third degree polynomial to the param_counts (independent 
    variable) and the losses (dependent variable) and using the 
    polynomial's derivative to detect when the interpolation 
    threshold curve has been reached. This will make 
    the spacing between the parameter counts differ depending 
    on how close the model is to exhibiting double descent.
    
    ...
    Parameters
    ----------
    param_counts : list or np.array of ints
        The list of prior parameter counts that the model was
        trained over
    losses : list or np.array of floats
        The list of final losses for each model with 
        corresponding paramter counts
    past_dd : bool
        Flag to indicate whether the interpolation threshold
        has been reached. Set to False by default.
    alpha : float
        Tuning paramter that increases or decreases the value of 
        the next parameter count
        
    Returns
    -------
    param_count : int
        The next parameter count
    past_dd : bool
        Flag that indicates whether the interpolation threshold
        has been reached. This should be used as the input for
        the next iteration of this algorithm
    """
    
    current_iter = param_counts[-1]
    
    if type(losses) != np.ndarray:
        losses = np.array(losses)
        
    if type(param_counts) != np.ndarray:
        param_counts = np.array(param_counts)
    
    # Create weight vector
    # We weight datapoints that are further away from
    # the current parameter count less (1/n) depending on
    # how many indices (n) away it is from the current one
    w = np.arange(1,len(param_counts) + 1, 1)[-1::-1]
    w = w/w.sum()
    
    poly = np.polyfit(param_counts[:], losses[:], 3, w=w)
    
    dy = 3*poly[0]*(current_iter - 10**-4)**2 + 2*poly[1]*(current_iter - 10**-4) + poly[2]
    
    # The current iteration of this adaptive parameter
    # count algorithm does not use the second derivative
    # dy2 = 6*poly[0]*(current_iter - 10**-3) + 2*poly[1]
    
    sgn = 1 if dy < 0 else 0
    
    if sgn == 0:
        past_dd = True
        
    next_count = sgn*max(alpha*dy, 3) + 1
    
    if sgn and past_dd:
        return ceil(next_count) + current_iter + 10, past_dd
    
    return ceil(next_count) + current_iter, past_dd


def get_parameter_counts_prob(mu, max_params, num_samples):
    """Generate a list of paramter counts using a normal distribution
    centered around the parameter count that signifies the interpolation
    threshold
    
    ...
    Parameters
    ----------
    mu : int
        The chosen value for the interpolation threshold
    max_params : int
        The desired maximum number of parameters to train up to. 
        The meaning of this will vary depending on the model and
        the dataset. 
        (Ex. The value max_params for an MLP training on MNIST would 
        mean max_params * 10^3 parameters will be the maximum number of 
        parameters)
    num_samples : int
        Desired number of parameter counts to be returned. (Note: 
        The number of parameter counts returned will not be exactly
        be num_samples because parameter counts must be integers, 
        and we are not allowing for duplicate parameter counts. 
        It will usually be between 3/4*num_samples and num_samples.
    
    Returns
    -------
    paramater_counts : list
        A sorted list of parameter counts to train over
    """
    
    sigma_est = approx_sigma(mu, max_params)
    
    # How many sigmas away from the mean is 0?
    # Use mu - w*sigma = 0
    # -> w = mu/sigma
    w = mu/sigma_est
    
    # What percentile is 0 in our distribution?
    # P[X <= mu - w*sigma] since mu - w*sigma = 0
    # -> P[X <= Z] where Z = ((mu - w*sigma) - mu)/sigma
    # So, Z = -w
    percentile = norm.cdf(-w)
    print(percentile)
    
    # Use this percentile to compensate for the amount of 
    # parameter_counts we lose when we turn sampels into ints 
    # and threshold > 0
    compensated_num_samples = int(round((1 + percentile)*num_samples, 0))
    dist = np.random.normal(loc=mu, scale=sigma_est, size=compensated_num_samples)
    dist = dist[dist>=0]
    parameter_counts = [int(round(x, 0)) for x in dist]
    return sorted(list(set(parameter_counts)))


def train_nn(model, dataloaders, optimizer, scheduler, num_epochs=100):
    """Trains a neural network
    
    ...
    Parameters
    ----------
    model
        A PyTorch neural network object (Only strict requirement is that 
        the object has a .forward() method)
    dataloaders : dict
        Dictionary in the format {"train": <train_loader>, "test": <test_loader>}
        where <train_loader> and <test_loader> are PyTorch Dataloaders
    criterion : torch.nn Loss Function
        Loss function that the neural network will use to train and validate the data
    optimizer : torch.optim optimizer
        Optimizer that model will use to minimize the loss
    num_epochs : int
        The number of training epochs that the model will train over. One epoch is
        one full pass through the train and test loaders
        
    Returns
    -------
    model
         A PyTorch neural network object that has been trained
    train_loss : list
        A list of all training losses at the end of each epoch
    test_acc : list
        A list of all test losses at the end of each epoch
    """
    

    writer = SummaryWriter('runs/dd_model_{}'.format(model.param_counts[model.current_count]))
    
    
    # get some random training images
    dataiter = iter(dataloaders['train'])
    images, labels = dataiter.next()

    # create grid of images
    img_grid = torchvision.utils.make_grid(images)

    # show images
    matplotlib_imshow(img_grid, one_channel=True)

    # write to tensorboard
    writer.add_image('MNIST Dataset', img_grid)
    writer.add_graph(model, images)
    writer.close()
    
    train_loss = []
    test_acc = []
    
    dataset_sizes = {'train': len(dataloaders['train'].dataset), 'test': len(dataloaders['test'].dataset) }

    model = model.cuda()
    
    optimizer = optim.SGD(model.parameters(), lr=.01, momentum=0.95)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=500, gamma=0.1)
    
    print('Model with parameter count {}'.format(model.param_counts[model.current_count]))
    print('-' * 10)
    
    for epoch in range(num_epochs):
            
        #print('Epoch {}/{}'.format(epoch + 1, num_epochs))
        # print('-' * 10)
        
        # Switches between training and testing sets
        for phase in ['train', 'test']:
            
            if phase == 'train':
                model.train()
                running_loss = 0.0
            elif phase == 'test':
                model.eval()   # Set model to evaluate mode
                running_test_loss = 0.0
                
            # Train/Test loop
            for i, d in enumerate(dataloaders[phase], 0):
                
                inputs, labels = d
                
                inputs = inputs.cuda()
                labels = labels.cuda()
                optimizer.zero_grad()

                if phase == 'train':
                    outputs = model.forward(inputs)
                    loss = model.loss(outputs, labels)
                    # backward + optimize only if in training phase
                    loss.backward()
                    optimizer.step()
                    # statistics
                    running_loss += loss.item() * inputs.size(0)

                if phase == 'test':
                    outputs = model.forward(inputs)
                    test_loss = model.loss(outputs, labels)
                    running_test_loss += test_loss.item() * inputs.size(0)
                    
                if i % 50 == 49:    # every 1000 mini-batches...

                    # ...log the running loss
                    writer.add_scalar('Training Loss',
                                    running_loss / 1000,
                                    epoch * len(dataloaders['train']) + i)

                    # ...log a Matplotlib Figure showing the model's predictions on a
                    # random mini-batch
                    writer.add_figure('Predictions vs. Actuals',
                                    plot_classes_preds(model, inputs, labels),
                                    global_step=epoch * len(dataloaders['train']) + i)

            if phase == 'train':
                scheduler.step()
                
        train_loss.append(running_loss/ dataset_sizes['train'])        
        test_acc.append(running_test_loss/ dataset_sizes['test'])
        
        if train_loss[-1] < 10**-5:
            break
                    
    print('Train Loss: {:.4f}\nTest Loss {:.4f}'.format(train_loss[-1], test_acc[-1]))
    
    return model, train_loss, test_acc


def dd_neural_network(model):
    """Uses the train_nn and get_next_param_count methods 
    to train the same architecture with varying parameter
    sizes. This method also keeps track of the final losses 
    of each model that is trained
    
    ...
    Parameters
    ----------
    model : Models instance
        The model object that will be trained with varying 
        parameter sizes
        
    Returns
    -------
    None
    """
    
    for index in range(len(model.param_counts)):
        
        model.input_layer = nn.Linear(model.data.data_x_dim * model.data.data_y_dim, 
                                 model.param_counts[index]*10**3)
        model.hidden_layer = nn.Linear(model.param_counts[index]*10**3, 10)

        _, train_loss, test_loss = train_nn(model, model.data.dataloaders
                                                ,'SGD', 'scheduler',
                                                  num_epochs=6000)

        model.losses['train'] = np.append(model.losses['train'], train_loss[-1])
        model.losses['test'] = np.append(model.losses['test'], test_loss[-1])

    model.current_count = len(model.param_counts) - 1
    flag = False
    post_flag = 0
    
    while post_flag < 4:

        next_ct, flag = get_next_param_count(model.param_counts, 
                                                 model.losses['test']/model.losses['test'].sum(), 
                                                 flag)

        model.param_counts = np.append(model.param_counts, next_ct)
        model.current_count += 1
        model.input_layer = nn.Linear(model.data.data_x_dim * model.data.data_y_dim, 
                                 model.param_counts[model.current_count]*10**3)
        model.hidden_layer = nn.Linear(model.param_counts[model.current_count]*10**3, 10)

        _, train_loss, test_loss = train_nn(model, model.data.dataloaders,
                                            'SGD', 'scheduler', num_epochs=6000)

        model.losses['train'] = np.append(model.losses['train'], train_loss[-1])
        model.losses['test'] = np.append(model.losses['test'], test_loss[-1])

        if flag and (model.param_counts[-1] - model.param_counts[-2]) != 1:
            post_flag += 1

        np.save('train_loss.npy', model.losses['train'])
        np.save('test_loss.npy', model.losses['test'])
        
        
def matplotlib_imshow(img, one_channel=False):
    if one_channel:
        img = img.mean(dim=0)
    img = img / 2 + 0.5     # unnormalize
    npimg = img.cpu().numpy()
    if one_channel:
        plt.imshow(npimg, cmap="plasma")
    else:
        plt.imshow(np.transpose(npimg, (1, 2, 0)))
        
        
        
def images_to_probs(net, images):
    '''
    Generates predictions and corresponding probabilities from a trained
    network and a list of images
    '''
    output = net(images)
    # convert output probabilities to predicted class
    _, preds_tensor = torch.max(output, 1)
    preds_tensor = preds_tensor.cpu()
    preds = np.squeeze(preds_tensor.numpy())
    return preds, [F.softmax(el, dim=0)[i].item() for i, el in zip(preds, output)]


def plot_classes_preds(net, images, labels):
    '''
    Generates matplotlib Figure using a trained network, along with images
    and labels from a batch, that shows the network's top prediction along
    with its probability, alongside the actual label, coloring this
    information based on whether the prediction was correct or not.
    Uses the "images_to_probs" function.
    '''
    preds, probs = images_to_probs(net, images)
    classes = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')
    # plot the images in the batch, along with predicted and true labels
    fig = plt.figure(figsize=(12, 48))
    for idx in np.arange(4):
        ax = fig.add_subplot(1, 4, idx+1, xticks=[], yticks=[])
        matplotlib_imshow(images[idx], one_channel=True)
        ax.set_title("{0}, {1:.1f}%\n(label: {2})".format(
            classes[preds[idx]],
            probs[idx] * 100.0,
            classes[labels[idx]]),
                    color=("green" if preds[idx]==labels[idx].item() else "red"))
    return fig