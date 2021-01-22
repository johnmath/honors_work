import torch.nn as nn
import torch.optim as optim
import data

class Models:
    """This class contains the attributes that all models have in common.
    
    ...
    
    Attributes
    ----------
        loss : str
            The loss function for the model. Options are {'L1', 'MSE', 
            'CrossEntropy'}.
        dataset : str
            The dataset that the model will be trained on. Options are 
            {'MNIST'}.
        cuda : bool
            If True, the model will train using GPU acceleration if a CUDA
            GPU is available. If False, the model will train on CPU
    """
    
    def __init__(self, loss, dataset, cuda):
        
        loss_functions = {'L1': nn.L1Loss(), 
                          'MSE': nn.MSELoss(), 
                          'CrossEntropy': nn.CrossEntropyLoss()}
        
        self.loss = loss_functions[loss]
        self.dataset = dataset
        self.cuda = cuda
        
    def train():
        pass
        
        
    
class MultilayerPerceptron(Models):
    """A Multilayer Perceptron with a single hidden layer of variable size
    
    ...
    
    Attributes
    ----------
        loss : str
            The loss function for the model. Options are {'L1', 'MSE',
            'CrossEntropy'}.
        dataset : str
            The dataset that the model will be trained on. Options are
            {'MNIST'}.
        cuda : bool
            If True, the model will train using GPU acceleration if a CUDA
            GPU is available. If False, the model will train on CPU
        optim : str
            The optimizer that the model will use while training. Options are
            {'SGD'}
    """
    
    def __init__(self, loss='MSE', dataset='MNIST', cuda=False, optim='SGD'):
        super(MultilayerPerceptron, self).__init__(loss, dataset, cuda)
    
        
        self.mlp_optim = optim.S
    
    

    
def train_nn(model, dataloaders, criterion, optimizer, num_epochs=100):
    """Trains a neural network
    
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
    
    train_loss = []
    test_acc = []
    
    dataset_sizes = {'train': len(dataloaders['train'].dataset), 'test': len(dataloaders['test'].dataset) }

    for epoch in range(num_epochs):
            
        print('Epoch {}/{}'.format(epoch + 1, num_epochs))
        print('-' * 10)
        
      # Switches between training and testing sets
        
        for phase in ['train', 'test']:
            
            if phase == 'train':
                model.train()
                running_loss = 0.0

            elif phase == 'test':
                model.eval()   # Set model to evaluate mode
                running_test_loss = 0.0

              # Train/Test loop

            for inputs, labels in dataloaders[phase]:

                inputs = inputs.cuda()
                labels = labels.cuda()

                optimizer.zero_grad()

                if phase == 'train':
                    with torch.set_grad_enabled(phase=='train'):
                        outputs = model(inputs)
                        loss = criterion(outputs, labels)
                        # backward + optimize only if in training phase
                        loss.backward()
                        optimizer.step()
                        # statistics
                        running_loss += loss.item() * inputs.size(0)

                if phase == 'test':

                    with torch.no_grad():
                        outputs = model(inputs)
                        test_loss = criterion(outputs, labels)
                        running_test_loss += test_loss.item() * inputs.size(0)


#                     if phase == 'train':
#                         scheduler.step()

        train_loss.append(running_loss/ dataset_sizes['train'])
        test_acc.append(running_test_loss/ dataset_sizes['test'])

        print('Train Loss: {:.4f}\nTest Loss {:.4f}'.format(train_loss[epoch], test_acc[epoch]))
            
    return model, train_loss, test_acc